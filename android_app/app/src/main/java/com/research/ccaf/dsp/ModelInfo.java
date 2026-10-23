package com.research.ccaf.dsp;

import java.io.Serializable;
import java.util.HashMap;
import java.util.Map;

/**
 * Model metadata and parameter container.
 */
public class ModelInfo implements Serializable {

    public enum ModelType {
        PROPOSED_CCAF_DB,
        DECOUPLED_ACI,
        NLMS_FAST,
        NLMS_SLOW,
        KWONG_VSS,
        BENESTY_VSS,
        CONVEX_COMBINATION,
        CUSTOM_IMPORTED
    }

    private final String id;
    private final String name;
    private final String category;
    private final String description;
    private final ModelType type;
    private final Map<String, Double> parameters;
    private final boolean isProposed;

    public ModelInfo(String id, String name, String category, String description,
                     ModelType type, Map<String, Double> parameters, boolean isProposed) {
        this.id = id;
        this.name = name;
        this.category = category;
        this.description = description;
        this.type = type;
        this.parameters = parameters != null ? parameters : new HashMap<>();
        this.isProposed = isProposed;
    }

    public String getId() { return id; }
    public String getName() { return name; }
    public String getCategory() { return category; }
    public String getDescription() { return description; }
    public ModelType getType() { return type; }
    public Map<String, Double> getParameters() { return parameters; }
    public boolean isProposed() { return isProposed; }

    public AdaptiveFilter createFilterInstance() {
        switch (type) {
            case PROPOSED_CCAF_DB: {
                int taps = getParamInt("taps", 64);
                double muMin = getParam("muMin", 0.05);
                double muMax = getParam("muMax", 0.50);
                double gamma = getParam("gamma", 0.005);
                double alpha = getParam("alpha", 0.10);
                double tau = getParam("tau", 0.04);
                double kappa = getParam("kappa", 8.0);
                return new CCAFDeadBandFilter(taps, muMin, muMax, gamma, alpha, tau, kappa);
            }
            case DECOUPLED_ACI: {
                int taps = getParamInt("taps", 64);
                double step = getParam("step", 0.05);
                double gamma = getParam("gamma", 0.005);
                double alpha = getParam("alpha", 0.10);
                return new DecoupledACIFilter(taps, step, gamma, alpha);
            }
            case NLMS_FAST:
                return NLMSFilter.createFast();
            case NLMS_SLOW:
                return NLMSFilter.createSlow();
            case KWONG_VSS: {
                int taps = getParamInt("taps", 64);
                double muMin = getParam("muMin", 0.005);
                double muMax = getParam("muMax", 0.50);
                double a = getParam("alphaVss", 0.97);
                double g = getParam("gammaVss", 0.05);
                return new KwongVSSFilter(taps, muMin, muMax, a, g);
            }
            case BENESTY_VSS: {
                int taps = getParamInt("taps", 64);
                double muMin = getParam("muMin", 0.01);
                double muMax = getParam("muMax", 0.50);
                double lambda = getParam("lambda", 0.98);
                return new BenestyVSSFilter(taps, muMin, muMax, lambda);
            }
            case CONVEX_COMBINATION:
                return new ConvexCombinationFilter();
            case CUSTOM_IMPORTED:
            default: {
                int taps = getParamInt("taps", 64);
                double muMin = getParam("muMin", 0.05);
                double muMax = getParam("muMax", 0.50);
                double gamma = getParam("gamma", 0.005);
                double alpha = getParam("alpha", 0.10);
                double tau = getParam("tau", 0.04);
                double kappa = getParam("kappa", 8.0);
                return new CCAFDeadBandFilter(taps, muMin, muMax, gamma, alpha, tau, kappa);
            }
        }
    }

    public double getParam(String key, double fallback) {
        Double val = parameters.get(key);
        return val != null ? val : fallback;
    }

    public int getParamInt(String key, int fallback) {
        Double val = parameters.get(key);
        return val != null ? val.intValue() : fallback;
    }
}
