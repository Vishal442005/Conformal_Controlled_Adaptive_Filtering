package com.research.ccaf.dsp;

import org.json.JSONObject;

import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;

/**
 * Singleton repository managing all research models and custom imported models.
 */
public class ModelManager {

    public interface OnModelChangeListener {
        void onModelChanged(ModelInfo newModel, AdaptiveFilter filterInstance);
    }

    private static ModelManager instance;

    private final List<ModelInfo> availableModels = new ArrayList<>();
    private final List<OnModelChangeListener> listeners = new ArrayList<>();
    private ModelInfo activeModelInfo;
    private AdaptiveFilter activeFilter;

    private ModelManager() {
        initDefaultModels();
    }

    public static synchronized ModelManager getInstance() {
        if (instance == null) {
            instance = new ModelManager();
        }
        return instance;
    }

    private void initDefaultModels() {
        // 1. Proposed CCAF-DB
        Map<String, Double> ccafParams = new HashMap<>();
        ccafParams.put("taps", 64.0);
        ccafParams.put("muMin", 0.05);
        ccafParams.put("muMax", 0.50);
        ccafParams.put("gamma", 0.005);
        ccafParams.put("alpha", 0.10);
        ccafParams.put("tau", 0.04);
        ccafParams.put("kappa", 8.0);
        ModelInfo proposedModel = new ModelInfo(
                "ccaf_db",
                "Proposed CCAF-DB",
                "PROPOSED METHOD",
                "Conformal-Controlled Adaptive Filter with Dead-Band step-size control. Combines 90% distribution-free coverage with rapid transient re-convergence.",
                ModelInfo.ModelType.PROPOSED_CCAF_DB,
                ccafParams,
                true
        );
        availableModels.add(proposedModel);

        // 2. Decoupled ACI
        Map<String, Double> aciParams = new HashMap<>();
        aciParams.put("taps", 64.0);
        aciParams.put("step", 0.05);
        aciParams.put("gamma", 0.005);
        aciParams.put("alpha", 0.10);
        availableModels.add(new ModelInfo(
                "decoupled_aci",
                "Decoupled ACI",
                "CONFORMAL BASELINE",
                "Adaptive Conformal Inference decoupled from step size. Fixed slow NLMS (mu=0.05) with 90% nonconformity tracking.",
                ModelInfo.ModelType.DECOUPLED_ACI,
                aciParams,
                false
        ));

        // 3. NLMS (fast)
        Map<String, Double> fastParams = new HashMap<>();
        fastParams.put("taps", 64.0);
        fastParams.put("step", 0.50);
        availableModels.add(new ModelInfo(
                "nlms_fast",
                "NLMS (fast)",
                "CLASSICAL POINT ESTIMATOR",
                "Normalized LMS with large step size (mu=0.50). Rapid tracking but high steady-state misadjustment.",
                ModelInfo.ModelType.NLMS_FAST,
                fastParams,
                false
        ));

        // 4. NLMS (slow)
        Map<String, Double> slowParams = new HashMap<>();
        slowParams.put("taps", 64.0);
        slowParams.put("step", 0.05);
        availableModels.add(new ModelInfo(
                "nlms_slow",
                "NLMS (slow)",
                "CLASSICAL POINT ESTIMATOR",
                "Normalized LMS with conservative step size (mu=0.05). Low steady-state EMSE floor but sluggish tracking.",
                ModelInfo.ModelType.NLMS_SLOW,
                slowParams,
                false
        ));

        // 5. Kwong VSS-LMS
        Map<String, Double> kwongParams = new HashMap<>();
        kwongParams.put("taps", 64.0);
        kwongParams.put("muMin", 0.005);
        kwongParams.put("muMax", 0.50);
        kwongParams.put("alphaVss", 0.97);
        kwongParams.put("gammaVss", 0.05);
        availableModels.add(new ModelInfo(
                "kwong_vss",
                "Kwong VSS-LMS",
                "VARIABLE STEP-SIZE",
                "Error-power driven variable step size LMS (Kwong & Johnston, 1992). Fast adaptation during transitions.",
                ModelInfo.ModelType.KWONG_VSS,
                kwongParams,
                false
        ));

        // 6. Benesty NP-VSS
        Map<String, Double> benestyParams = new HashMap<>();
        benestyParams.put("taps", 64.0);
        benestyParams.put("muMin", 0.01);
        benestyParams.put("muMax", 0.50);
        benestyParams.put("lambda", 0.98);
        availableModels.add(new ModelInfo(
                "benesty_vss",
                "Benesty NP-VSS",
                "VARIABLE STEP-SIZE",
                "Nonparametric VSS NLMS (Benesty et al., 2006). Step size regulated by noise-to-error power ratio.",
                ModelInfo.ModelType.BENESTY_VSS,
                benestyParams,
                false
        ));

        // 7. Convex Combination
        Map<String, Double> convexParams = new HashMap<>();
        convexParams.put("taps", 64.0);
        convexParams.put("muFast", 0.50);
        convexParams.put("muSlow", 0.05);
        convexParams.put("muA", 0.10);
        availableModels.add(new ModelInfo(
                "convex_comb",
                "Convex Combination",
                "COMBINATION FILTER",
                "Sigmoidal convex combination of fast (mu=0.50) and slow (mu=0.05) adaptive filters (Arenas-Garcia et al.).",
                ModelInfo.ModelType.CONVEX_COMBINATION,
                convexParams,
                false
        ));

        // Set proposed model active by default
        selectModel(proposedModel);
    }

    public List<ModelInfo> getAvailableModels() {
        return Collections.unmodifiableList(availableModels);
    }

    public ModelInfo getActiveModelInfo() {
        return activeModelInfo;
    }

    public AdaptiveFilter getActiveFilter() {
        return activeFilter;
    }

    public void selectModel(ModelInfo model) {
        this.activeModelInfo = model;
        this.activeFilter = model.createFilterInstance();
        notifyListeners();
    }

    public boolean selectModelById(String id) {
        for (ModelInfo info : availableModels) {
            if (info.getId().equalsIgnoreCase(id)) {
                selectModel(info);
                return true;
            }
        }
        return false;
    }

    /**
     * Parse and register a new custom model imported from a JSON file.
     */
    public ModelInfo addNewModelFromJson(String jsonContent) throws Exception {
        JSONObject obj = new JSONObject(jsonContent);
        String id = "custom_" + System.currentTimeMillis();
        String name = obj.optString("name", "Custom Imported Model");
        String category = obj.optString("category", "USER IMPORTED");
        String description = obj.optString("description", "Imported custom configuration file");

        Map<String, Double> params = new HashMap<>();
        if (obj.has("parameters")) {
            JSONObject pObj = obj.getJSONObject("parameters");
            Iterator<String> keys = pObj.keys();
            while (keys.hasNext()) {
                String k = keys.next();
                params.put(k, pObj.getDouble(k));
            }
        }

        ModelInfo customModel = new ModelInfo(
                id, name, category, description,
                ModelInfo.ModelType.CUSTOM_IMPORTED,
                params, false
        );

        availableModels.add(customModel);
        selectModel(customModel);
        return customModel;
    }

    public void addListener(OnModelChangeListener listener) {
        if (!listeners.contains(listener)) {
            listeners.add(listener);
        }
    }

    public void removeListener(OnModelChangeListener listener) {
        listeners.remove(listener);
    }

    private void notifyListeners() {
        for (OnModelChangeListener listener : listeners) {
            listener.onModelChanged(activeModelInfo, activeFilter);
        }
    }
}
