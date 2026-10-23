package com.research.ccaf.dsp;

import android.media.AudioFormat;
import android.media.AudioManager;
import android.media.AudioRecord;
import android.media.AudioTrack;
import android.media.MediaRecorder;
import android.util.Log;

import java.util.ArrayList;
import java.util.List;

/**
 * High-performance real-time AudioRecord and AudioTrack engine.
 * Records microphone audio, routes it through the active AdaptiveFilter,
 * buffers both original and filtered samples, and delivers waveform callbacks.
 */
public class AudioRecordPlayerEngine {

    private static final String TAG = "AudioEngine";
    public static final int SAMPLE_RATE = 16000;
    private static final int CHANNEL_CONFIG = AudioFormat.CHANNEL_IN_MONO;
    private static final int AUDIO_FORMAT = AudioFormat.ENCODING_PCM_16BIT;

    public interface AudioFrameListener {
        void onAudioFrame(double[] originalWindow, double[] filteredWindow, AdaptiveFilter.Output latestOutput);
    }

    private AudioRecord audioRecord;
    private AudioTrack activePlayer;
    private Thread recordingThread;
    private Thread playbackThread;

    private volatile boolean isRecording = false;
    private volatile boolean isPlaying = false;

    private final List<Double> recordedRawList = new ArrayList<>(SAMPLE_RATE * 10);
    private final List<Double> recordedFilteredList = new ArrayList<>(SAMPLE_RATE * 10);
    private AudioFrameListener frameListener;

    public void setFrameListener(AudioFrameListener listener) {
        this.frameListener = listener;
    }

    /**
     * Start live microphone recording and real-time adaptive filtering.
     */
    public synchronized boolean startRecording() {
        if (isRecording) return true;

        int minBufferSize = AudioRecord.getMinBufferSize(SAMPLE_RATE, CHANNEL_CONFIG, AUDIO_FORMAT);
        int bufferSize = Math.max(minBufferSize, 2048);

        try {
            audioRecord = new AudioRecord(
                    MediaRecorder.AudioSource.MIC,
                    SAMPLE_RATE,
                    CHANNEL_CONFIG,
                    AUDIO_FORMAT,
                    bufferSize
            );

            if (audioRecord.getState() != AudioRecord.STATE_INITIALIZED) {
                Log.e(TAG, "AudioRecord failed to initialize");
                return false;
            }

            recordedRawList.clear();
            recordedFilteredList.clear();

            AdaptiveFilter filter = ModelManager.getInstance().getActiveFilter();
            if (filter != null) {
                filter.reset();
            }

            audioRecord.startRecording();
            isRecording = true;

            recordingThread = new Thread(this::recordLoop, "CCAF-AudioRecord-Thread");
            recordingThread.start();
            return true;
        } catch (SecurityException se) {
            Log.e(TAG, "Missing RECORD_AUDIO permission", se);
            return false;
        } catch (Exception e) {
            Log.e(TAG, "Exception starting audio recording", e);
            return false;
        }
    }

    private void recordLoop() {
        short[] shortBuffer = new short[512];
        AdaptiveFilter filter = ModelManager.getInstance().getActiveFilter();

        double[] displayOriginal = new double[256];
        double[] displayFiltered = new double[256];
        int displayCounter = 0;
        AdaptiveFilter.Output lastOutput = null;

        while (isRecording && audioRecord != null) {
            int readCount = audioRecord.read(shortBuffer, 0, shortBuffer.length);
            if (readCount > 0) {
                for (int i = 0; i < readCount; i++) {
                    double rawSample = shortBuffer[i] / 32768.0;

                    // Filter sample
                    AdaptiveFilter.Output out = null;
                    if (filter != null) {
                        out = filter.process(rawSample);
                    } else {
                        out = new AdaptiveFilter.Output(rawSample, 0, rawSample, rawSample - 0.1, rawSample + 0.1, 0.05, false);
                    }
                    lastOutput = out;

                    synchronized (recordedRawList) {
                        recordedRawList.add(rawSample);
                        // Store the filtered/cleaned audio (the error signal in line-enhancer mode)
                        recordedFilteredList.add(out.error);
                    }

                    // Feed rolling display window
                    displayOriginal[displayCounter] = rawSample;
                    displayFiltered[displayCounter] = out.error;
                    displayCounter++;

                    if (displayCounter >= displayOriginal.length) {
                        displayCounter = 0;
                        if (frameListener != null) {
                            frameListener.onAudioFrame(
                                    displayOriginal.clone(),
                                    displayFiltered.clone(),
                                    lastOutput
                            );
                        }
                    }
                }
            }
        }
    }

    /**
     * Stop microphone recording.
     */
    public synchronized void stopRecording() {
        isRecording = false;
        if (recordingThread != null) {
            try {
                recordingThread.join(500);
            } catch (InterruptedException ignored) {}
            recordingThread = null;
        }

        if (audioRecord != null) {
            try {
                if (audioRecord.getState() == AudioRecord.STATE_INITIALIZED) {
                    audioRecord.stop();
                }
                audioRecord.release();
            } catch (Exception ignored) {}
            audioRecord = null;
        }
    }

    public boolean isRecording() {
        return isRecording;
    }

    /**
     * Get recorded raw audio samples as double array.
     */
    public double[] getRecordedRawAudio() {
        synchronized (recordedRawList) {
            double[] arr = new double[recordedRawList.size()];
            for (int i = 0; i < arr.length; i++) {
                arr[i] = recordedRawList.get(i);
            }
            return arr;
        }
    }

    /**
     * Get recorded model-filtered audio samples as double array.
     */
    public double[] getRecordedFilteredAudio() {
        synchronized (recordedFilteredList) {
            double[] arr = new double[recordedFilteredList.size()];
            for (int i = 0; i < arr.length; i++) {
                arr[i] = recordedFilteredList.get(i);
            }
            return arr;
        }
    }

    /**
     * Playback audio array using AudioTrack.
     */
    public synchronized void playAudio(final double[] samples, final Runnable onComplete) {
        stopPlayback();
        if (samples == null || samples.length == 0) return;

        isPlaying = true;
        playbackThread = new Thread(() -> {
            int minBufferSize = AudioTrack.getMinBufferSize(
                    SAMPLE_RATE,
                    AudioFormat.CHANNEL_OUT_MONO,
                    AudioFormat.ENCODING_PCM_16BIT
            );

            AudioTrack track = new AudioTrack(
                    AudioManager.STREAM_MUSIC,
                    SAMPLE_RATE,
                    AudioFormat.CHANNEL_OUT_MONO,
                    AudioFormat.ENCODING_PCM_16BIT,
                    Math.max(minBufferSize, 4096),
                    AudioTrack.MODE_STREAM
            );

            activePlayer = track;
            track.play();

            short[] pcmChunk = new short[512];
            int offset = 0;

            while (isPlaying && offset < samples.length) {
                int toWrite = Math.min(pcmChunk.length, samples.length - offset);
                for (int i = 0; i < toWrite; i++) {
                    double s = Math.max(-1.0, Math.min(1.0, samples[offset + i]));
                    pcmChunk[i] = (short) (s * 32767.0);
                }
                track.write(pcmChunk, 0, toWrite);
                offset += toWrite;
            }

            try {
                track.stop();
                track.release();
            } catch (Exception ignored) {}

            isPlaying = false;
            activePlayer = null;
            if (onComplete != null) {
                onComplete.run();
            }
        }, "CCAF-Playback-Thread");

        playbackThread.start();
    }

    /**
     * Stop any active playback.
     */
    public synchronized void stopPlayback() {
        isPlaying = false;
        if (activePlayer != null) {
            try {
                activePlayer.pause();
                activePlayer.flush();
                activePlayer.stop();
            } catch (Exception ignored) {}
            activePlayer = null;
        }
        if (playbackThread != null) {
            try {
                playbackThread.join(300);
            } catch (InterruptedException ignored) {}
            playbackThread = null;
        }
    }

    public boolean isPlaying() {
        return isPlaying;
    }
}
