package com.research.ccaf.dsp;

/**
 * Benesty et al. (2006) Nonparametric Variable Step-Size NLMS (NP-VSS).
 * Computes step size from the ratio of estimated system noise power to error power:
 * mu(n) = muMax * max(0, 1 - sigma_v^2(n) / sigma_e^2(n)).
 */
public class BenestyVSSFilter extends AbstractAdaptiveFilter {

    private final double muMin;
    private final double muMax;
    private final double lambda;
    private final double regDelta;

    private double currentStepSize;
    private double sigmaE2;
    private double sigmaV2;
    private static final double GAUSSIAN_Z_90 = 1.645;

    public BenestyVSSFilter(int tapLength, double muMin, double muMax, double lambda) {
        super(tapLength);
        this.muMin = muMin;
        this.muMax = muMax;
        this.lambda = lambda;
        this.regDelta = 1e-4;

        this.currentStepSize = muMin;
        this.sigmaE2 = 1e-2;
        this.sigmaV2 = 1e-3;
    }

    public BenestyVSSFilter() {
        this(64, 0.01, 0.50, 0.98);
    }

    @Override
    public Output process(double inputSample) {
        double desired = inputSample;

        double estimated = computeInnerProduct();
        double error = desired - estimated;

        // Recursive estimation of error power: sigma_e^2(n) = lambda * sigma_e^2(n-1) + (1-lambda)*e^2(n)
        sigmaE2 = lambda * sigmaE2 + (1.0 - lambda) * (error * error);

        // Update noise power floor estimate
        if (sigmaE2 < sigmaV2 * 1.5) {
            sigmaV2 = 0.999 * sigmaV2 + 0.001 * sigmaE2;
        }

        // Benesty NP-VSS formula: mu(n) = muMax * [1 - sigma_v^2 / sigma_e^2]
        double ratio = sigmaV2 / Math.max(sigmaE2, 1e-7);
        double factor = Math.max(0.0, 1.0 - ratio);
        currentStepSize = Math.max(muMin, Math.min(muMax, muMax * factor));

        // NLMS weight update
        double energy = computeRegressorEnergy() + regDelta;
        double normalizedStep = currentStepSize / energy;
        int idx = bufferIndex;
        for (int i = 0; i < tapLength; i++) {
            idx = (idx - 1 + tapLength) % tapLength;
            weights[i] += normalizedStep * error * regressorBuffer[idx];
        }

        pushRegressorSample(desired);

        // Scale and Gaussian bounds
        double scale = Math.sqrt(Math.max(1e-8, sigmaE2));
        double halfWidth = GAUSSIAN_Z_90 * scale;
        double lowerBound = estimated - halfWidth;
        double upperBound = estimated + halfWidth;

        boolean isMiss = (desired < lowerBound || desired > upperBound);
        updateStatistics(desired, lowerBound, upperBound, 0.10);

        return new Output(desired, estimated, error, lowerBound, upperBound, currentStepSize, isMiss);
    }

    @Override
    public void reset() {
        super.reset();
        this.currentStepSize = muMin;
        this.sigmaE2 = 1e-2;
        this.sigmaV2 = 1e-3;
    }

    @Override
    public String getName() {
        return "Benesty NP-VSS";
    }

    @Override
    public String getDescription() {
        return "Benesty Nonparametric Variable Step-Size NLMS. Modulates step size based on residual error power vs estimated background noise.";
    }

    @Override
    public String getCategory() {
        return "VSS BASELINE";
    }

    @Override
    public double getCurrentStepSize() {
        return currentStepSize;
    }
}
