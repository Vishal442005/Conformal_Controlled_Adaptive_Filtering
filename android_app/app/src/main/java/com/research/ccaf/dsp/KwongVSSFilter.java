package com.research.ccaf.dsp;

/**
 * Kwong & Johnston (1992) Variable Step-Size LMS (VSS-LMS).
 * Step-size adapts proportionally to squared instantaneous error:
 * mu(n+1) = alpha_vss * mu(n) + gamma_vss * e^2(n), clipped to [muMin, muMax].
 */
public class KwongVSSFilter extends AbstractAdaptiveFilter {

    private final double muMin;
    private final double muMax;
    private final double alphaVss;
    private final double gammaVss;
    private final double regDelta;
    private double currentStepSize;
    private static final double GAUSSIAN_Z_90 = 1.645;

    public KwongVSSFilter(int tapLength, double muMin, double muMax, double alphaVss, double gammaVss) {
        super(tapLength);
        this.muMin = muMin;
        this.muMax = muMax;
        this.alphaVss = alphaVss;
        this.gammaVss = gammaVss;
        this.regDelta = 1e-4;
        this.currentStepSize = muMin;
    }

    public KwongVSSFilter() {
        this(64, 0.005, 0.50, 0.97, 0.05);
    }

    @Override
    public Output process(double inputSample) {
        double desired = inputSample;

        double estimated = computeInnerProduct();
        double error = desired - estimated;

        runningVariance = varianceSmoothing * runningVariance + (1.0 - varianceSmoothing) * (error * error);
        double scale = Math.sqrt(runningVariance + 1e-8);

        // Standard LMS / Normalized weight update with VSS
        double energy = computeRegressorEnergy() + regDelta;
        double normalizedStep = currentStepSize / energy;
        int idx = bufferIndex;
        for (int i = 0; i < tapLength; i++) {
            idx = (idx - 1 + tapLength) % tapLength;
            weights[i] += normalizedStep * error * regressorBuffer[idx];
        }

        pushRegressorSample(desired);

        // Kwong VSS update: mu(n+1) = alpha * mu(n) + gamma * e^2(n)
        currentStepSize = alphaVss * currentStepSize + gammaVss * (error * error);
        currentStepSize = Math.max(muMin, Math.min(muMax, currentStepSize));

        // 90% Gaussian confidence interval
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
    }

    @Override
    public String getName() {
        return "Kwong VSS-LMS";
    }

    @Override
    public String getDescription() {
        return "Kwong-Johnston Variable Step-Size LMS. Adapts step size directly via squared error power; sensitive to impulsive bursts.";
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
