package com.research.ccaf.ui;

import android.Manifest;
import android.content.pm.PackageManager;
import android.os.Bundle;
import android.os.Environment;
import android.os.Handler;
import android.os.Looper;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.TextView;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;
import androidx.fragment.app.Fragment;

import com.research.ccaf.R;
import com.research.ccaf.dsp.AdaptiveFilter;
import com.research.ccaf.dsp.AudioRecordPlayerEngine;
import com.research.ccaf.dsp.ModelInfo;
import com.research.ccaf.dsp.ModelManager;
import com.research.ccaf.dsp.WavFileHelper;

import java.io.File;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;

/**
 * Option 1: Live Record Screen.
 * Records live audio from microphone, runs real-time filtering with active model,
 * renders live 2-line dual waveform, and provides post-recording playback and save options.
 */
public class LiveRecordFragment extends Fragment implements AudioRecordPlayerEngine.AudioFrameListener {

    private static final int REQUEST_RECORD_PERMISSION = 201;

    private DualWaveformView waveformView;
    private Button btnRecordToggle;
    private Button btnListenReal;
    private Button btnListenModel;
    private Button btnSave;
    private TextView tvActiveModelTag;
    private TextView tvMetrics;
    private TextView tvStatus;

    private AudioRecordPlayerEngine audioEngine;
    private final Handler mainHandler = new Handler(Looper.getMainLooper());

    private double[] lastRecordedRaw;
    private double[] lastRecordedFiltered;

    @Nullable
    @Override
    public View onCreateView(@NonNull LayoutInflater inflater, @Nullable ViewGroup container, @Nullable Bundle savedInstanceState) {
        View view = inflater.inflate(R.layout.fragment_live_record, container, false);

        waveformView = view.findViewById(R.id.liveWaveformView);
        btnRecordToggle = view.findViewById(R.id.btnRecordToggle);
        btnListenReal = view.findViewById(R.id.btnListenReal);
        btnListenModel = view.findViewById(R.id.btnListenModel);
        btnSave = view.findViewById(R.id.btnSave);
        tvActiveModelTag = view.findViewById(R.id.tvActiveModelTag);
        tvMetrics = view.findViewById(R.id.tvMetrics);
        tvStatus = view.findViewById(R.id.tvStatus);

        audioEngine = new AudioRecordPlayerEngine();
        audioEngine.setFrameListener(this);

        setupListeners();
        updateActiveModelDisplay();

        ModelManager.getInstance().addListener((newModel, filterInstance) -> {
            if (isAdded()) {
                mainHandler.post(this::updateActiveModelDisplay);
            }
        });

        return view;
    }

    private void updateActiveModelDisplay() {
        ModelInfo active = ModelManager.getInstance().getActiveModelInfo();
        if (active != null) {
            tvActiveModelTag.setText("Active Model: " + active.getName() + " [" + active.getCategory() + "]");
        }
    }

    private void setupListeners() {
        btnRecordToggle.setOnClickListener(v -> {
            if (audioEngine.isRecording()) {
                stopLiveRecording();
            } else {
                checkPermissionAndStartRecording();
            }
        });

        btnListenReal.setOnClickListener(v -> {
            if (lastRecordedRaw == null || lastRecordedRaw.length == 0) {
                Toast.makeText(getContext(), "No recorded audio available", Toast.LENGTH_SHORT).show();
                return;
            }
            tvStatus.setText("Playing: Real Raw Audio (Microphone)...");
            btnListenReal.setEnabled(false);
            btnListenModel.setEnabled(false);
            audioEngine.playAudio(lastRecordedRaw, () -> mainHandler.post(() -> {
                tvStatus.setText("Playback complete.");
                btnListenReal.setEnabled(true);
                btnListenModel.setEnabled(true);
            }));
        });

        btnListenModel.setOnClickListener(v -> {
            if (lastRecordedFiltered == null || lastRecordedFiltered.length == 0) {
                Toast.makeText(getContext(), "No filtered audio available", Toast.LENGTH_SHORT).show();
                return;
            }
            tvStatus.setText("Playing: Changed Audio (After Model)...");
            btnListenReal.setEnabled(false);
            btnListenModel.setEnabled(false);
            audioEngine.playAudio(lastRecordedFiltered, () -> mainHandler.post(() -> {
                tvStatus.setText("Playback complete.");
                btnListenReal.setEnabled(true);
                btnListenModel.setEnabled(true);
            }));
        });

        btnSave.setOnClickListener(v -> saveRecordingsToStorage());
    }

    private void checkPermissionAndStartRecording() {
        if (ContextCompat.checkSelfPermission(requireContext(), Manifest.permission.RECORD_AUDIO)
                != PackageManager.PERMISSION_GRANTED) {
            ActivityCompat.requestPermissions(requireActivity(),
                    new String[]{Manifest.permission.RECORD_AUDIO}, REQUEST_RECORD_PERMISSION);
            return;
        }
        startLiveRecording();
    }

    private void startLiveRecording() {
        audioEngine.stopPlayback();
        boolean started = audioEngine.startRecording();
        if (started) {
            btnRecordToggle.setText("STOP RECORDING");
            btnRecordToggle.setBackgroundColor(0xFFDC2626); // Alert Red
            tvStatus.setText("Recording in progress... Live filtering active.");
            btnListenReal.setEnabled(false);
            btnListenModel.setEnabled(false);
            btnSave.setEnabled(false);
        } else {
            Toast.makeText(getContext(), "Failed to open microphone", Toast.LENGTH_SHORT).show();
        }
    }

    private void stopLiveRecording() {
        audioEngine.stopRecording();
        btnRecordToggle.setText("START LIVE RECORDING");
        btnRecordToggle.setBackgroundColor(0xFF0284C7); // Vibrant Blue
        tvStatus.setText("Recording stopped. Select an option below.");

        lastRecordedRaw = audioEngine.getRecordedRawAudio();
        lastRecordedFiltered = audioEngine.getRecordedFilteredAudio();

        boolean hasData = (lastRecordedRaw != null && lastRecordedRaw.length > 0);
        btnListenReal.setEnabled(hasData);
        btnListenModel.setEnabled(hasData);
        btnSave.setEnabled(hasData);

        if (hasData) {
            Toast.makeText(getContext(), "Recorded " + (lastRecordedRaw.length / AudioRecordPlayerEngine.SAMPLE_RATE) + "s audio", Toast.LENGTH_SHORT).show();
        }
    }

    private void saveRecordingsToStorage() {
        if (lastRecordedRaw == null || lastRecordedRaw.length == 0) return;

        try {
            File storageDir = requireContext().getExternalFilesDir(Environment.DIRECTORY_MUSIC);
            if (storageDir == null) {
                storageDir = requireContext().getFilesDir();
            }

            String timestamp = new SimpleDateFormat("yyyyMMdd_HHmmss", Locale.US).format(new Date());
            File rawFile = new File(storageDir, "LiveRecord_Real_" + timestamp + ".wav");
            File filteredFile = new File(storageDir, "LiveRecord_Model_" + timestamp + ".wav");

            WavFileHelper.saveWavFile(rawFile, lastRecordedRaw, AudioRecordPlayerEngine.SAMPLE_RATE);
            WavFileHelper.saveWavFile(filteredFile, lastRecordedFiltered, AudioRecordPlayerEngine.SAMPLE_RATE);

            Toast.makeText(getContext(), "Saved to:\n" + rawFile.getName() + "\n" + filteredFile.getName(), Toast.LENGTH_LONG).show();
            tvStatus.setText("Files saved: " + filteredFile.getName());
        } catch (Exception e) {
            Toast.makeText(getContext(), "Error saving files: " + e.getMessage(), Toast.LENGTH_SHORT).show();
        }
    }

    @Override
    public void onAudioFrame(double[] originalWindow, double[] filteredWindow, AdaptiveFilter.Output latestOutput) {
        mainHandler.post(() -> {
            if (waveformView != null) {
                waveformView.updateData(originalWindow, filteredWindow);
            }
            if (latestOutput != null && tvMetrics != null) {
                AdaptiveFilter filter = ModelManager.getInstance().getActiveFilter();
                double cov = (filter != null) ? filter.getEmpiricalCoverage() : 0.0;
                double wink = (filter != null) ? filter.getWinklerScore() : 0.0;
                tvMetrics.setText(String.format(Locale.US,
                        "Step Size mu: %.4f | Coverage: %.1f%% | Winkler: %.3f",
                        latestOutput.stepSize, cov, wink));
            }
        });
    }

    @Override
    public void onPause() {
        super.onPause();
        if (audioEngine != null) {
            audioEngine.stopRecording();
            audioEngine.stopPlayback();
        }
    }
}
