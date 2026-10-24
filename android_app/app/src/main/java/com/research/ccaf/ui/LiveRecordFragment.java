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
import com.research.ccaf.dsp.UniversalAudioHelper;
import com.research.ccaf.dsp.WavFileHelper;

import java.io.File;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;

/**
 * Option 1: Live Record Screen.
 * Records live audio from microphone, runs real-time filtering with active model,
 * renders live 2-line dual waveform, provides instant zero-latency A/B shifting
 * during post-recording playback, and saves multi-format audio to storage.
 */
public class LiveRecordFragment extends Fragment implements AudioRecordPlayerEngine.AudioFrameListener {

    private static final int REQUEST_RECORD_PERMISSION = 201;

    private DualWaveformView waveformView;
    private Button btnRecordToggle;
    private Button btnListenReal;
    private Button btnListenModel;
    private Button btnPlaySeamlessLive;
    private Button btnSave;
    private TextView tvActiveModelTag;
    private TextView tvMetrics;
    private TextView tvStatus;

    private AudioRecordPlayerEngine audioEngine;
    private final UniversalAudioHelper.SeamlessShifterEngine shifterEngine = new UniversalAudioHelper.SeamlessShifterEngine();
    private final Handler mainHandler = new Handler(Looper.getMainLooper());

    private double[] lastRecordedRaw;
    private double[] lastRecordedFiltered;
    private double runningPowerRaw = 1e-6;
    private double runningPowerFilt = 1e-6;

    @Nullable
    @Override
    public View onCreateView(@NonNull LayoutInflater inflater, @Nullable ViewGroup container, @Nullable Bundle savedInstanceState) {
        View view = inflater.inflate(R.layout.fragment_live_record, container, false);

        waveformView = view.findViewById(R.id.liveWaveformView);
        btnRecordToggle = view.findViewById(R.id.btnRecordToggle);
        btnListenReal = view.findViewById(R.id.btnListenReal);
        btnListenModel = view.findViewById(R.id.btnListenModel);
        btnPlaySeamlessLive = view.findViewById(R.id.btnPlaySeamlessLive);
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

        // Instant A/B Shift: Switch to Original
        btnListenReal.setOnClickListener(v -> {
            shifterEngine.shiftToOriginal();
            btnListenReal.setBackgroundColor(0xFF0F766E); // Teal active
            btnListenReal.setTextColor(0xFFFFFFFF);
            btnListenModel.setBackgroundColor(0xFF334155); // Gray inactive
            btnListenModel.setTextColor(0xFFCBD5E1);
            tvStatus.setText("🎧 Live Track: 🔈 ORIGINAL MICROPHONE");
        });

        // Instant A/B Shift: Switch to Model Filtered
        btnListenModel.setOnClickListener(v -> {
            shifterEngine.shiftToModel();
            btnListenModel.setBackgroundColor(0xFFD97706); // Amber active
            btnListenModel.setTextColor(0xFFFFFFFF);
            btnListenReal.setBackgroundColor(0xFF334155);  // Gray inactive
            btnListenReal.setTextColor(0xFFCBD5E1);
            tvStatus.setText("🎧 Live Track: ⚡ MODEL FILTERED");
        });

        // Seamless Dual-Track Playback
        if (btnPlaySeamlessLive != null) {
            btnPlaySeamlessLive.setOnClickListener(v -> {
                if (!shifterEngine.isPlaying()) {
                    if (lastRecordedRaw == null || lastRecordedFiltered == null) return;
                    shifterEngine.startSeamlessPlayback(lastRecordedRaw, lastRecordedFiltered, AudioRecordPlayerEngine.SAMPLE_RATE, () -> mainHandler.post(() -> {
                        btnPlaySeamlessLive.setText("▶️ PLAY RECORDING (ENABLES LIVE SHIFTING)");
                        tvStatus.setText("Playback finished.");
                    }));
                    btnPlaySeamlessLive.setText("⏹️ STOP PLAYBACK");
                    tvStatus.setText("Playing: Tap buttons above to shift between Real and Model in real time!");
                } else {
                    shifterEngine.stop();
                    btnPlaySeamlessLive.setText("▶️ PLAY RECORDING (ENABLES LIVE SHIFTING)");
                    tvStatus.setText("Playback stopped.");
                }
            });
        }

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
        shifterEngine.stop();
        boolean started = audioEngine.startRecording();
        if (started) {
            btnRecordToggle.setText("STOP RECORDING");
            btnRecordToggle.setBackgroundColor(0xFFDC2626); // Alert Red
            tvStatus.setText("Recording in progress... Live adaptive filter actively tracking.");
            btnListenReal.setEnabled(false);
            btnListenModel.setEnabled(false);
            if (btnPlaySeamlessLive != null) btnPlaySeamlessLive.setEnabled(false);
            btnSave.setEnabled(false);
        } else {
            Toast.makeText(getContext(), "Failed to open microphone", Toast.LENGTH_SHORT).show();
        }
    }

    private void stopLiveRecording() {
        audioEngine.stopRecording();
        btnRecordToggle.setText("START LIVE RECORDING");
        btnRecordToggle.setBackgroundColor(0xFF0284C7); // Vibrant Blue
        tvStatus.setText("Recording stopped. Tap Play Recording and test A/B shifting!");

        lastRecordedRaw = audioEngine.getRecordedRawAudio();
        lastRecordedFiltered = audioEngine.getRecordedFilteredAudio();

        boolean hasData = (lastRecordedRaw != null && lastRecordedRaw.length > 0);
        btnListenReal.setEnabled(hasData);
        btnListenModel.setEnabled(hasData);
        if (btnPlaySeamlessLive != null) btnPlaySeamlessLive.setEnabled(hasData);
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

            Toast.makeText(getContext(), "Saved to:\n" + filteredFile.getName(), Toast.LENGTH_LONG).show();
            tvStatus.setText("Saved to: " + filteredFile.getName());
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

                // Track ERLE power
                runningPowerRaw = 0.95 * runningPowerRaw + 0.05 * (latestOutput.desired * latestOutput.desired);
                runningPowerFilt = 0.95 * runningPowerFilt + 0.05 * (latestOutput.error * latestOutput.error);
                double erle = 10.0 * Math.log10(Math.max(1e-6, runningPowerRaw) / Math.max(1e-6, runningPowerFilt));

                double surge = Math.abs(latestOutput.error) / Math.max(1e-4, (latestOutput.upperBound - latestOutput.lowerBound) / 3.29);
                String deadBand = (cov >= 90.0) ? "SLEEP" : "ACTIVE";

                tvMetrics.setText(String.format(Locale.US,
                        "Step Size μ: %.4f | Coverage: %.1f%% | Winkler: %.3f\nERLE: %+.1f dB | Surge: %.2f σ | Dead-band: %s | FLOPs: 133",
                        latestOutput.stepSize, cov, wink, erle, surge, deadBand));
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
        shifterEngine.stop();
    }
}
