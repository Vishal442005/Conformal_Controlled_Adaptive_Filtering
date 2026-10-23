package com.research.ccaf.dsp;

import android.content.Context;
import android.media.AudioFormat;
import android.media.AudioManager;
import android.media.AudioTrack;
import android.media.MediaCodec;
import android.media.MediaExtractor;
import android.media.MediaFormat;
import android.net.Uri;
import android.util.Log;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.ShortBuffer;

/**
 * Universal Audio Decoder, Exporter, and Seamless Shifter.
 * Supports decoding all Android-supported audio containers:
 * WAV, MP3, AAC, M4A, OGG/Opus, FLAC.
 * Also provides zero-latency cross-fade shifting between Original and Model audio.
 */
public class UniversalAudioHelper {

    private static final String TAG = "UniversalAudioHelper";

    public static class DecodedAudio {
        public final int sampleRate;
        public final int channels;
        public final double[] samples; // Normalized [-1.0, 1.0]

        public DecodedAudio(int sampleRate, int channels, double[] samples) {
            this.sampleRate = sampleRate;
            this.channels = channels;
            this.samples = samples;
        }
    }

    /**
     * Decode any audio file or content URI using Android's native MediaCodec / MediaExtractor.
     * Fallback to direct 16-bit PCM WAV reader if MediaCodec is unneeded.
     */
    public static DecodedAudio decodeAudioUri(Context context, Uri uri) throws IOException {
        MediaExtractor extractor = new MediaExtractor();
        try {
            extractor.setDataSource(context, uri, null);
        } catch (Exception e) {
            // Direct stream fallback for raw WAV
            InputStream is = context.getContentResolver().openInputStream(uri);
            if (is != null) {
                WavFileHelper.WavData wav = WavFileHelper.readWav(is);
                return new DecodedAudio(wav.sampleRate, wav.channels, wav.samples);
            }
            throw new IOException("Cannot open audio source: " + e.getMessage());
        }

        int trackIndex = -1;
        MediaFormat format = null;
        for (int i = 0; i < extractor.getTrackCount(); i++) {
            MediaFormat mf = extractor.getTrackFormat(i);
            String mime = mf.getString(MediaFormat.KEY_MIME);
            if (mime != null && mime.startsWith("audio/")) {
                trackIndex = i;
                format = mf;
                break;
            }
        }

        if (trackIndex < 0 || format == null) {
            extractor.release();
            throw new IOException("No audio track found in file.");
        }

        extractor.selectTrack(trackIndex);
        String mime = format.getString(MediaFormat.KEY_MIME);
        MediaCodec codec = MediaCodec.createDecoderByType(mime);
        codec.configure(format, null, null, 0);
        codec.start();

        int sampleRate = format.getInteger(MediaFormat.KEY_SAMPLE_RATE);
        int channelCount = format.getInteger(MediaFormat.KEY_CHANNEL_COUNT);

        ByteArrayOutputStream pcmStream = new ByteArrayOutputStream();
        MediaCodec.BufferInfo info = new MediaCodec.BufferInfo();
        boolean sawInputEOS = false;
        boolean sawOutputEOS = false;

        final long TIMEOUT_US = 5000;

        while (!sawOutputEOS) {
            if (!sawInputEOS) {
                int inputBufIndex = codec.dequeueInputBuffer(TIMEOUT_US);
                if (inputBufIndex >= 0) {
                    ByteBuffer dstBuf = codec.getInputBuffer(inputBufIndex);
                    int sampleSize = extractor.readSampleData(dstBuf, 0);
                    if (sampleSize < 0) {
                        codec.queueInputBuffer(inputBufIndex, 0, 0, 0L, MediaCodec.BUFFER_FLAG_END_OF_STREAM);
                        sawInputEOS = true;
                    } else {
                        long presentationTimeUs = extractor.getSampleTime();
                        codec.queueInputBuffer(inputBufIndex, 0, sampleSize, presentationTimeUs, 0);
                        extractor.advance();
                    }
                }
            }

            int res = codec.dequeueOutputBuffer(info, TIMEOUT_US);
            if (res >= 0) {
                if ((info.flags & MediaCodec.BUFFER_FLAG_END_OF_STREAM) != 0) {
                    sawOutputEOS = true;
                }
                if (info.size > 0) {
                    ByteBuffer outBuf = codec.getOutputBuffer(res);
                    outBuf.position(info.offset);
                    outBuf.limit(info.offset + info.size);
                    byte[] chunk = new byte[info.size];
                    outBuf.get(chunk);
                    pcmStream.write(chunk, 0, chunk.length);
                }
                codec.releaseOutputBuffer(res, false);
            }
        }

        codec.stop();
        codec.release();
        extractor.release();

        byte[] rawBytes = pcmStream.toByteArray();
        int totalShorts = rawBytes.length / 2;
        double[] monoSamples;

        ByteBuffer bb = ByteBuffer.wrap(rawBytes).order(ByteOrder.LITTLE_ENDIAN);
        ShortBuffer sb = bb.asShortBuffer();

        if (channelCount >= 2) {
            int monoLength = totalShorts / channelCount;
            monoSamples = new double[monoLength];
            for (int i = 0; i < monoLength; i++) {
                double sum = 0.0;
                for (int c = 0; c < channelCount; c++) {
                    sum += sb.get();
                }
                monoSamples[i] = (sum / channelCount) / 32768.0;
            }
        } else {
            monoSamples = new double[totalShorts];
            for (int i = 0; i < totalShorts; i++) {
                monoSamples[i] = sb.get() / 32768.0;
            }
        }

        return new DecodedAudio(sampleRate, 1, monoSamples);
    }

    /**
     * Seamless Instant Audio Shifter Engine.
     * Keeps two continuous tracks running synchronously, instantaneously cross-fading
     * between "Original" (gain 1.0, 0.0) and "Model" (gain 0.0, 1.0) with zero restart.
     */
    public static class SeamlessShifterEngine {
        private AudioTrack audioTrack;
        private Thread playbackThread;
        private volatile boolean isRunning = false;
        private volatile float targetModelMix = 0.0f; // 0.0 = 100% Original, 1.0 = 100% Model
        private float currentModelMix = 0.0f;

        public void startSeamlessPlayback(double[] orig, double[] model, int sampleRate, Runnable onComplete) {
            stop();
            if (orig == null || model == null) return;

            final int len = Math.min(orig.length, model.length);
            final int minBuf = AudioTrack.getMinBufferSize(sampleRate, AudioFormat.CHANNEL_OUT_MONO, AudioFormat.ENCODING_PCM_16BIT);

            audioTrack = new AudioTrack(
                    AudioManager.STREAM_MUSIC,
                    sampleRate,
                    AudioFormat.CHANNEL_OUT_MONO,
                    AudioFormat.ENCODING_PCM_16BIT,
                    Math.max(minBuf, 4096),
                    AudioTrack.MODE_STREAM
            );

            isRunning = true;
            audioTrack.play();

            playbackThread = new Thread(() -> {
                short[] buffer = new short[512];
                int offset = 0;

                while (isRunning && offset < len) {
                    int chunkSize = Math.min(buffer.length, len - offset);
                    for (int i = 0; i < chunkSize; i++) {
                        // Smooth 10ms crossfade interpolation to prevent click artifacts
                        currentModelMix += (targetModelMix - currentModelMix) * 0.05f;

                        double sOrig = orig[offset + i];
                        double sModel = model[offset + i];
                        double blended = (1.0f - currentModelMix) * sOrig + (currentModelMix) * sModel;

                        blended = Math.max(-1.0, Math.min(1.0, blended));
                        buffer[i] = (short) (blended * 32767.0);
                    }
                    audioTrack.write(buffer, 0, chunkSize);
                    offset += chunkSize;
                }

                try {
                    audioTrack.stop();
                    audioTrack.release();
                } catch (Exception ignored) {}
                isRunning = false;

                if (onComplete != null) {
                    onComplete.run();
                }
            }, "SeamlessShifterThread");

            playbackThread.start();
        }

        public void shiftToOriginal() {
            targetModelMix = 0.0f;
        }

        public void shiftToModel() {
            targetModelMix = 1.0f;
        }

        public boolean isPlaying() {
            return isRunning;
        }

        public void stop() {
            isRunning = false;
            if (audioTrack != null) {
                try {
                    audioTrack.pause();
                    audioTrack.flush();
                    audioTrack.stop();
                    audioTrack.release();
                } catch (Exception ignored) {}
                audioTrack = null;
            }
            if (playbackThread != null) {
                try {
                    playbackThread.join(250);
                } catch (Exception ignored) {}
                playbackThread = null;
            }
        }
    }
}
