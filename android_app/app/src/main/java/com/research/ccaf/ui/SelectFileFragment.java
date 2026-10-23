package com.research.ccaf.ui;

import android.net.Uri;
import android.os.Bundle;
import android.os.Environment;
import android.os.Handler;
import android.os.Looper;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;

import androidx.activity.result.ActivityResultLauncher;
import androidx.activity.result.contract.ActivityResultContracts;
import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.fragment.app.Fragment;

import com.research.ccaf.R;
import com.research.ccaf.dsp.AdaptiveFilter;
import com.research.ccaf.dsp.ModelInfo;
import com.research.ccaf.dsp.ModelManager;
import com.research.ccaf.dsp.UniversalAudioHelper;
import com.research.ccaf.dsp.WavFileHelper;

import java.io.File;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;

/**
 * Option 2: Select File Screen.
 * Accepts any audio format (WAV, MP3, AAC, FLAC, M4A, OGG),
 * applies the active model, displays a real-time dual-line waveform,
 * allows instant zero-latency shifting between Original and Model during live playback,
 * and exports the processed audio file to storage.
 */
public class SelectFileFragment extends Fragment {

    private DualWaveformView fileWaveformView;
    private Button btnSelectFile;
    private Button btnShiftOriginal;
    private Button btnShiftModel;
    private Button btnPlaySeamless;
    private Button btnSaveNewFile;
    private TextView tvFileInfo;
    private TextView tvActiveModelTag;
    private TextView tvProcessingStats;
    private ProgressBar progressBar;

    private final UniversalAudioHelper.SeamlessShifterEngine shifterEngine = new UniversalAudioHelper.SeamlessShifterEngine();
    private final Handler mainHandler = new Handler(Looper.getMainLooper());

    private double[] originalSamples;
    private double[] modelProcessedSamples;
    private int sampleRate = 16000;
    private String loadedFileName = "No file chosen";

    // Launch picker for all audio types
    private final ActivityResultLauncher<String> filePickerLauncher =
            registerForActivityResult(new ActivityResultContracts.GetContent(), this::onFileSelected);

    @Nullable
    @Override
    public View onCreateView(@NonNull LayoutInflater inflater, @Nullable ViewGroup container, @Nullable Bundle savedInstanceState) {
        View view = inflater.inflate(R.layout.fragment_select_file, container, false);

        fileWaveformView = view.findViewById(R.id.fileWaveformView);
        btnSelectFile = view.findViewById(R.id.btnSelectFile);
        btnShiftOriginal = view.findViewById(R.id.btnShiftOriginal);
        btnShiftModel = view.findViewById(R.id.btnShiftModel);
        btnPlaySeamless = view.findViewById(R.id.btnPlaySeamless);
        btnSaveNewFile = view.findViewById(R.id.btnSaveNewFile);
        tvFileInfo = view.findViewById(R.id.tvFileInfo);
        tvActiveModelTag = view.findViewById(R.id.tvActiveModelTagFile);
        tvProcessingStats = view.findViewById(R.id.tvProcessingStats);
        progressBar = view.findViewById(R.id.progressBar);

        setupListeners();
        updateModelTag();

        ModelManager.getInstance().addListener((newModel, filterInstance) -> {
            if (isAdded()) {
                mainHandler.post(() -> {
                    updateModelTag();
                    if (originalSamples != null && originalSamples.length > 0) {
                        applyActiveModelToFile();
                    }
                });
            }
        });

        return view;
    }

    private void updateModelTag() {
        ModelInfo active = ModelManager.getInstance().getActiveModelInfo();
        if (active != null) {
            tvActiveModelTag.setText("Active Model: " + active.getName() + " (" + active.getCategory() + ")");
        }
    }

    private void setupListeners() {
        // Universal Audio selection (accepts audio/*, wav, mp3, aac, flac, etc.)
        btnSelectFile.setOnClickListener(v -> filePickerLauncher.launch("audio/*"));

        // Instant Shifter: Shift to Original
        btnShiftOriginal.setOnClickListener(v -> {
            shifterEngine.shiftToOriginal();
            btnShiftOriginal.setBackgroundColor(0xFF0F766E); // Active Teal
            btnShiftOriginal.setTextColor(0xFFFFFFFF);
            btnShiftModel.setBackgroundColor(0xFF334155);    // Inactive Gray
            btnShiftModel.setTextColor(0xFFCBD5E1);
            tvProcessingStats.setText("🎧 Audio Track: 🔈 ORIGINAL AUDIO");
        });

        // Instant Shifter: Shift to Model
        btnShiftModel.setOnClickListener(v -> {
            shifterEngine.shiftToModel();
            btnShiftModel.setBackgroundColor(0xFFD97706);    // Active Amber
            btnShiftModel.setTextColor(0xFFFFFFFF);
            btnShiftOriginal.setBackgroundColor(0xFF334155); // Inactive Gray
            btnShiftOriginal.setTextColor(0xFFCBD5E1);
            tvProcessingStats.setText("🎧 Audio Track: ⚡ MODEL FILTERED");
        });

        // Play / Stop Seamless Playback
        btnPlaySeamless.setOnClickListener(v -> {
            if (!shifterEngine.isPlaying()) {
                if (originalSamples == null || modelProcessedSamples == null) return;
                shifterEngine.startSeamlessPlayback(originalSamples, modelProcessedSamples, sampleRate, () -> mainHandler.post(() -> {
                    btnPlaySeamless.setText("▶️ PLAY AUDIO (ENABLES LIVE SHIFTING)");
                    tvProcessingStats.setText("Playback complete.");
                }));
                btnPlaySeamless.setText("⏹️ STOP PLAYBACK");
                tvProcessingStats.setText("Playing: Tap buttons above to shift between Original and Model in real time!");
            } else {
                shifterEngine.stop();
                btnPlaySeamless.setText("▶️ PLAY AUDIO (ENABLES LIVE SHIFTING)");
                tvProcessingStats.setText("Playback stopped.");
            }
        });

        // Save New File
        btnSaveNewFile.setOnClickListener(v -> saveProcessedAudioFile());
    }

    private void onFileSelected(Uri uri) {
        if (uri == null) return;

        progressBar.setVisibility(View.VISIBLE);
        tvFileInfo.setText("Decoding audio file (universal decoder)...");

        new Thread(() -> {
            try {
                // Decode using Universal Decoder (WAV, MP3, AAC, FLAC, M4A, OGG)
                UniversalAudioHelper.DecodedAudio decoded = UniversalAudioHelper.decodeAudioUri(requireContext(), uri);
                originalSamples = decoded.samples;
                sampleRate = decoded.sampleRate;
                loadedFileName = uri.getLastPathSegment();
                if (loadedFileName == null) loadedFileName = "SelectedAudio";

                mainHandler.post(() -> {
                    tvFileInfo.setText("Loaded: " + loadedFileName + " (" + (originalSamples.length / sampleRate) + "s, " + sampleRate + " Hz)");
                    applyActiveModelToFile();
                });
            } catch (Exception e) {
                mainHandler.post(() -> {
                    progressBar.setVisibility(View.GONE);
                    Toast.makeText(getContext(), "Error opening audio: " + e.getMessage(), Toast.LENGTH_LONG).show();
                    tvFileInfo.setText("Failed to decode audio. Please check file format.");
                });
            }
        }).start();
    }

    private void applyActiveModelToFile() {
        if (originalSamples == null || originalSamples.length == 0) return;

        progressBar.setVisibility(View.VISIBLE);
        tvProcessingStats.setText("Applying active model in real-time...");

        new Thread(() -> {
            AdaptiveFilter filter = ModelManager.getInstance().getActiveFilter();
            if (filter != null) {
                filter.reset();
            }

            modelProcessedSamples = new double[originalSamples.length];

            int displayPoints = 300;
            double[] displayOrig = new double[displayPoints];
            double[] displayModel = new double[displayPoints];
            int step = Math.max(1, originalSamples.length / displayPoints);

            for (int i = 0; i < originalSamples.length; i++) {
                double raw = originalSamples[i];
                AdaptiveFilter.Output out = (filter != null) ? filter.process(raw) : null;
                double cleaned = (out != null) ? out.error : raw;
                modelProcessedSamples[i] = cleaned;

                int displayIdx = i / step;
                if (displayIdx < displayPoints && i % step == 0) {
                    displayOrig[displayIdx] = raw;
                    displayModel[displayIdx] = cleaned;
                }
            }

            mainHandler.post(() -> {
                progressBar.setVisibility(View.GONE);
                fileWaveformView.updateData(displayOrig, displayModel);

                btnPlaySeamless.setEnabled(true);
                btnSaveNewFile.setEnabled(true);

                double cov = (filter != null) ? filter.getEmpiricalCoverage() : 0.0;
                double wink = (filter != null) ? filter.getWinklerScore() : 0.0;
                tvProcessingStats.setText(String.format(Locale.US,
                        "Processing Complete. Coverage: %.2f%% | Winkler: %.3f. Ready for Instant Shifting!",
                        cov, wink));
            });
        }).start();
    }

    private void saveProcessedAudioFile() {
        if (modelProcessedSamples == null || modelProcessedSamples.length == 0) return;

        try {
            File storageDir = requireContext().getExternalFilesDir(Environment.DIRECTORY_MUSIC);
            if (storageDir == null) {
                storageDir = requireContext().getFilesDir();
            }

            String timestamp = new SimpleDateFormat("yyyyMMdd_HHmmss", Locale.US).format(new Date());
            File destinationFile = new File(storageDir, "Model_Filtered_" + timestamp + ".wav");

            WavFileHelper.saveWavFile(destinationFile, modelProcessedSamples, sampleRate);
            Toast.makeText(getContext(), "Saved to storage:\n" + destinationFile.getAbsolutePath(), Toast.LENGTH_LONG).show();
            tvProcessingStats.setText("Saved to: " + destinationFile.getName());
        } catch (Exception e) {
            Toast.makeText(getContext(), "Error saving file: " + e.getMessage(), Toast.LENGTH_SHORT).show();
        }
    }

    @Override
    public void onPause() {
        super.onPause();
        shifterEngine.stop();
    }

    @Override
    public void onDestroy() {
        super.onDestroy();
        shifterEngine.stop();
    }
}
