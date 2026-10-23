package com.research.ccaf.dsp;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;

/**
 * Standard 16-bit Linear PCM WAV reader and writer.
 */
public class WavFileHelper {

    public static class WavData {
        public final int sampleRate;
        public final int channels;
        public final double[] samples; // Normalized [-1.0, 1.0]

        public WavData(int sampleRate, int channels, double[] samples) {
            this.sampleRate = sampleRate;
            this.channels = channels;
            this.samples = samples;
        }
    }

    /**
     * Read audio samples from a WAV file or stream.
     */
    public static WavData readWav(InputStream inputStream) throws IOException {
        byte[] header = new byte[44];
        int readHeader = inputStream.read(header);
        if (readHeader < 44) {
            throw new IOException("File too short for valid WAV header");
        }

        // Validate RIFF header
        if (header[0] != 'R' || header[1] != 'I' || header[2] != 'F' || header[3] != 'F') {
            throw new IOException("Not a valid RIFF file");
        }

        ByteBuffer bb = ByteBuffer.wrap(header).order(ByteOrder.LITTLE_ENDIAN);
        int channels = bb.getShort(22);
        int sampleRate = bb.getInt(24);
        int bitsPerSample = bb.getShort(34);

        if (bitsPerSample != 16) {
            throw new IOException("Only 16-bit PCM WAV currently supported, got: " + bitsPerSample + " bits");
        }

        ByteArrayOutputStream buffer = new ByteArrayOutputStream();
        byte[] chunk = new byte[4096];
        int bytesRead;
        while ((bytesRead = inputStream.read(chunk)) != -1) {
            buffer.write(chunk, 0, bytesRead);
        }
        byte[] audioBytes = buffer.toByteArray();

        int totalSamples = audioBytes.length / 2;
        double[] samples;
        if (channels == 2) {
            // Downmix stereo to mono
            int monoLength = totalSamples / 2;
            samples = new double[monoLength];
            ByteBuffer audioBuffer = ByteBuffer.wrap(audioBytes).order(ByteOrder.LITTLE_ENDIAN);
            for (int i = 0; i < monoLength; i++) {
                short left = audioBuffer.getShort();
                short right = audioBuffer.getShort();
                samples[i] = ((left + right) / 2.0) / 32768.0;
            }
        } else {
            samples = new double[totalSamples];
            ByteBuffer audioBuffer = ByteBuffer.wrap(audioBytes).order(ByteOrder.LITTLE_ENDIAN);
            for (int i = 0; i < totalSamples; i++) {
                short s = audioBuffer.getShort();
                samples[i] = s / 32768.0;
            }
        }

        return new WavData(sampleRate, 1, samples);
    }

    public static WavData readWavFile(File file) throws IOException {
        try (FileInputStream fis = new FileInputStream(file)) {
            return readWav(fis);
        }
    }

    /**
     * Save normalized audio samples [-1.0, 1.0] to a standard 16-bit mono WAV file.
     */
    public static void saveWavFile(File file, double[] samples, int sampleRate) throws IOException {
        try (FileOutputStream fos = new FileOutputStream(file)) {
            writeWavToStream(fos, samples, sampleRate);
        }
    }

    public static void writeWavToStream(OutputStream out, double[] samples, int sampleRate) throws IOException {
        int channels = 1;
        int bitsPerSample = 16;
        int byteRate = sampleRate * channels * (bitsPerSample / 8);
        int blockAlign = channels * (bitsPerSample / 8);
        int subChunk2Size = samples.length * (bitsPerSample / 8);
        int chunkSize = 36 + subChunk2Size;

        ByteBuffer header = ByteBuffer.allocate(44).order(ByteOrder.LITTLE_ENDIAN);
        // RIFF header
        header.put((byte) 'R').put((byte) 'I').put((byte) 'F').put((byte) 'F');
        header.putInt(chunkSize);
        header.put((byte) 'W').put((byte) 'A').put((byte) 'V').put((byte) 'E');

        // fmt chunk
        header.put((byte) 'f').put((byte) 'm').put((byte) 't').put((byte) ' ');
        header.putInt(16); // Subchunk1Size for PCM
        header.putShort((short) 1); // AudioFormat: 1 = PCM
        header.putShort((short) channels);
        header.putInt(sampleRate);
        header.putInt(byteRate);
        header.putShort((short) blockAlign);
        header.putShort((short) bitsPerSample);

        // data chunk
        header.put((byte) 'd').put((byte) 'a').put((byte) 't').put((byte) 'a');
        header.putInt(subChunk2Size);

        out.write(header.array());

        // Audio sample data
        byte[] pcmData = new byte[samples.length * 2];
        ByteBuffer sampleBuffer = ByteBuffer.wrap(pcmData).order(ByteOrder.LITTLE_ENDIAN);
        for (double sample : samples) {
            double clamped = Math.max(-1.0, Math.min(1.0, sample));
            short pcm = (short) (clamped * 32767.0);
            sampleBuffer.putShort(pcm);
        }
        out.write(pcmData);
        out.flush();
    }
}
