package com.research.ccaf.ui;

import android.net.Uri;
import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.RadioGroup;
import android.widget.TextView;
import android.widget.Toast;

import androidx.activity.result.ActivityResultLauncher;
import androidx.activity.result.contract.ActivityResultContracts;
import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.fragment.app.Fragment;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import com.research.ccaf.R;
import com.research.ccaf.dsp.ModelInfo;
import com.research.ccaf.dsp.ModelManager;

import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.util.HashMap;
import java.util.Map;

/**
 * Option 3: Choose Model Screen.
 * Provides 2 interfaces:
 *  1. Add New Model (Import model JSON from files or create custom parameter set)
 *  2. Select Model (List of all 7 research models + proposed model + imported models)
 */
public class ChooseModelFragment extends Fragment {

    private RadioGroup rgInterfaceToggle;
    private LinearLayout layoutAddNewModel;
    private LinearLayout layoutSelectModel;

    // Interface 1: Add New Model
    private Button btnImportFromFile;
    private Button btnCreateManualModel;
    private EditText etModelName;
    private EditText etTaps;
    private EditText etMuMin;
    private EditText etMuMax;
    private EditText etGamma;
    private EditText etAlpha;
    private EditText etDeadband;
    private TextView tvImportStatus;

    // Interface 2: Select Model
    private RecyclerView rvModels;
    private ModelAdapter modelAdapter;
    private TextView tvCurrentActiveHeader;

    private final ActivityResultLauncher<String> jsonFilePickerLauncher =
            registerForActivityResult(new ActivityResultContracts.GetContent(), this::onJsonFileSelected);

    @Nullable
    @Override
    public View onCreateView(@NonNull LayoutInflater inflater, @Nullable ViewGroup container, @Nullable Bundle savedInstanceState) {
        View view = inflater.inflate(R.layout.fragment_choose_model, container, false);

        rgInterfaceToggle = view.findViewById(R.id.rgInterfaceToggle);
        layoutAddNewModel = view.findViewById(R.id.layoutAddNewModel);
        layoutSelectModel = view.findViewById(R.id.layoutSelectModel);

        // Sub-interface 1 views
        btnImportFromFile = view.findViewById(R.id.btnImportFromFile);
        btnCreateManualModel = view.findViewById(R.id.btnCreateManualModel);
        etModelName = view.findViewById(R.id.etModelName);
        etTaps = view.findViewById(R.id.etTaps);
        etMuMin = view.findViewById(R.id.etMuMin);
        etMuMax = view.findViewById(R.id.etMuMax);
        etGamma = view.findViewById(R.id.etGamma);
        etAlpha = view.findViewById(R.id.etAlpha);
        etDeadband = view.findViewById(R.id.etDeadband);
        tvImportStatus = view.findViewById(R.id.tvImportStatus);

        // Sub-interface 2 views
        rvModels = view.findViewById(R.id.rvModels);
        tvCurrentActiveHeader = view.findViewById(R.id.tvCurrentActiveHeader);

        setupInterfaceToggle();
        setupSelectModelList();
        setupAddNewModelListeners();
        updateActiveHeader();

        return view;
    }

    private void setupInterfaceToggle() {
        rgInterfaceToggle.setOnCheckedChangeListener((group, checkedId) -> {
            if (checkedId == R.id.rbTabSelectModel) {
                layoutSelectModel.setVisibility(View.VISIBLE);
                layoutAddNewModel.setVisibility(View.GONE);
                updateActiveHeader();
            } else if (checkedId == R.id.rbTabAddNewModel) {
                layoutSelectModel.setVisibility(View.GONE);
                layoutAddNewModel.setVisibility(View.VISIBLE);
            }
        });
    }

    private void setupSelectModelList() {
        rvModels.setLayoutManager(new LinearLayoutManager(getContext()));
        modelAdapter = new ModelAdapter(ModelManager.getInstance().getAvailableModels(), model -> {
            ModelManager.getInstance().selectModel(model);
            updateActiveHeader();
            Toast.makeText(getContext(), "Activated model: " + model.getName(), Toast.LENGTH_SHORT).show();
        });
        rvModels.setAdapter(modelAdapter);
    }

    private void updateActiveHeader() {
        ModelInfo active = ModelManager.getInstance().getActiveModelInfo();
        if (active != null) {
            tvCurrentActiveHeader.setText("Currently Selected: " + active.getName() + " (" + active.getCategory() + ")");
        }
    }

    private void setupAddNewModelListeners() {
        // 1. Import from files
        btnImportFromFile.setOnClickListener(v -> jsonFilePickerLauncher.launch("application/json"));

        // 2. Create custom model manually
        btnCreateManualModel.setOnClickListener(v -> {
            try {
                String name = etModelName.getText().toString().trim();
                if (name.isEmpty()) name = "Custom CCAF Filter";

                int taps = Integer.parseInt(etTaps.getText().toString().trim());
                double muMin = Double.parseDouble(etMuMin.getText().toString().trim());
                double muMax = Double.parseDouble(etMuMax.getText().toString().trim());
                double gamma = Double.parseDouble(etGamma.getText().toString().trim());
                double alpha = Double.parseDouble(etAlpha.getText().toString().trim());
                double tau = Double.parseDouble(etDeadband.getText().toString().trim());

                JSONObject json = new JSONObject();
                json.put("name", name);
                json.put("category", "USER CONFIGURED");
                json.put("description", "User-configured CCAF adaptive filter with custom parameters.");

                JSONObject params = new JSONObject();
                params.put("taps", (double) taps);
                params.put("muMin", muMin);
                params.put("muMax", muMax);
                params.put("gamma", gamma);
                params.put("alpha", alpha);
                params.put("tau", tau);
                params.put("kappa", 8.0);
                json.put("parameters", params);

                ModelInfo added = ModelManager.getInstance().addNewModelFromJson(json.toString());
                modelAdapter.notifyDataSetChanged();
                tvImportStatus.setText("Successfully created and activated: " + added.getName());
                Toast.makeText(getContext(), "Created: " + added.getName(), Toast.LENGTH_SHORT).show();

                // Switch back to select tab
                rgInterfaceToggle.check(R.id.rbTabSelectModel);
            } catch (Exception e) {
                Toast.makeText(getContext(), "Error creating model: " + e.getMessage(), Toast.LENGTH_SHORT).show();
            }
        });
    }

    private void onJsonFileSelected(Uri uri) {
        if (uri == null) return;
        try {
            InputStream is = requireContext().getContentResolver().openInputStream(uri);
            BufferedReader reader = new BufferedReader(new InputStreamReader(is));
            StringBuilder sb = new StringBuilder();
            String line;
            while ((line = reader.readLine()) != null) {
                sb.append(line).append("\n");
            }
            reader.close();

            ModelInfo imported = ModelManager.getInstance().addNewModelFromJson(sb.toString());
            modelAdapter.notifyDataSetChanged();
            tvImportStatus.setText("Imported and activated: " + imported.getName());
            Toast.makeText(getContext(), "Imported successfully: " + imported.getName(), Toast.LENGTH_SHORT).show();

            // Switch to list tab
            rgInterfaceToggle.check(R.id.rbTabSelectModel);
        } catch (Exception e) {
            Toast.makeText(getContext(), "Failed to import JSON model: " + e.getMessage(), Toast.LENGTH_LONG).show();
            tvImportStatus.setText("Import failed: " + e.getMessage());
        }
    }
}
