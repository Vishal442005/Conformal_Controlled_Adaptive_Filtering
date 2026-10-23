package com.research.ccaf.dsp;

/**
 * Normalized Least Mean Squares (NLMS) filter with Gaussian confidence bounds.
 * Configured as fast (mu=0.50) or slow (mu=0.05).
 */
public class NLMSFilter extends AbstractAdaptiveFilter {

    private final double stepSize;
    private final boolean isFast;
    private final double regDelta;
    private static final double GAUSSIAN_Z_90 = 1.645;

    public NLMSFilter(int tapLength, double stepSize, boolean isFast) {
        super(tapLength);
        this.stepSize = stepSize;
        this.isFast = isFast;
        this.regDelta = 1e-4;
    }

    public static NLMSFilter createFast() {
        return new NLMSFilter(64, 0.50, true);
    }

    public static NLMSFilter createSlow() {
        return new NLMSFilter(64, 0.05, false);
    }

    @Override
    public Output process(double inputSample) {
        double desired = inputSample;

        double estimated = computeInnerProduct();
        double error = desired - estimated;

        // Running residual scale for Gaussian confidence interval
        runningVariance = varianceSmoothing * runningVariance + (1.0 - varianceSmoothing) * (error * error);
        double scale = Math.sqrt(runningVariance + 1e-8);

        // Standard NLMS weight update
        double energy = computeRegressorEnergy() + regDelta;
        double normalizedStep = stepSize / energy;
        int idx = bufferIndex;
        for (int i = 0; i < tapLength; i++) {
            idx = (idx - 1 + tapLength) % tapLength;
            weights[i] += normalizedStep * error * regressorBuffer[idx];
        }

        pushRegressorSample(desired);

        // Standard textbook 90% Gaussian prediction interval
        double halfWidth = GAUSSIAN_Z_90 * scale;
        double lowerBound = estimated - halfWidth;
        double upperBound = estimated + halfWidth;

        boolean isMiss = (desired < lowerBound || desired > upperBound);
        updateStatistics(desired, lowerBound, upperBound, 0.10);

        return new Output(desired, estimated, error, lowerBound, upperBound, stepSize, isMiss);
    }

    @Override
    public String getName() {
        return isFast ? "NLMS (fast)" : "NLMS (slow)";
    }

    @Override
    public String getDescription() {
        return isFast
                ? "Fast Normalized LMS (mu=0.50). High tracking agility, but elevated steady-state misadjustment."
                : "Slow Normalized LMS (mu=0.05). Low steady-state EMSE floor, but sluggish recovery under plant shifts.";
    }

    @Override
    public String getCategory() {
        return "CLASSICAL BASELINE";
    }

    @Override
    public double getCurrentStepSize() {
        return stepSize;
    }
}
