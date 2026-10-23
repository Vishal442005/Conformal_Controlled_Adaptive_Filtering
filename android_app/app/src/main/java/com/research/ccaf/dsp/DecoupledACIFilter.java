package com.research.ccaf.dsp;

/**
 * Decoupled Adaptive Conformal Inference (ACI) baseline.
 * Uses a fixed slow NLMS filter for point estimation and runs ACI independently
 * without closing the feedback loop into the step size.
 */
public class DecoupledACIFilter extends AbstractAdaptiveFilter {

    private final double stepSize;
    private final double gamma;
    private final double alpha;
    private final double regDelta;

    private double conformalQuantile;

    public DecoupledACIFilter(int tapLength, double stepSize, double gamma, double alpha) {
        super(tapLength);
        this.stepSize = stepSize;
        this.gamma = gamma;
        this.alpha = alpha;
        this.regDelta = 1e-4;
        this.conformalQuantile = 1.645;
    }

    public DecoupledACIFilter() {
        this(64, 0.05, 0.005, 0.10);
    }

    @Override
    public Output process(double inputSample) {
        double desired = inputSample;

        // Point estimation
        double estimated = computeInnerProduct();
        double error = desired - estimated;

        // Dispersion scale
        runningVariance = varianceSmoothing * runningVariance + (1.0 - varianceSmoothing) * (error * error);
        double scale = Math.sqrt(runningVariance + 1e-8);

        // Score and miscoverage indicator
        double score = Math.abs(error) / scale;
        boolean isMiss = (score > conformalQuantile);
        double missIndicator = isMiss ? 1.0 : 0.0;

        // Decoupled ACI recursion (open-loop, no step-size feedback)
        conformalQuantile = Math.max(0.1, conformalQuantile + gamma * (alpha - missIndicator));

        // Fixed NLMS weight update
        double energy = computeRegressorEnergy() + regDelta;
        double normalizedStep = stepSize / energy;
        int idx = bufferIndex;
        for (int i = 0; i < tapLength; i++) {
            idx = (idx - 1 + tapLength) % tapLength;
            weights[i] += normalizedStep * error * regressorBuffer[idx];
        }

        pushRegressorSample(desired);

        double halfWidth = conformalQuantile * scale;
        double lowerBound = estimated - halfWidth;
        double upperBound = estimated + halfWidth;

        updateStatistics(desired, lowerBound, upperBound, alpha);

        return new Output(desired, estimated, error, lowerBound, upperBound, stepSize, isMiss);
    }

    @Override
    public void reset() {
        super.reset();
        this.conformalQuantile = 1.645;
    }

    @Override
    public String getName() {
        return "Decoupled ACI";
    }

    @Override
    public String getDescription() {
        return "Open-loop Adaptive Conformal Inference with fixed slow NLMS (mu=0.05). Quantile tracking is decoupled from weight updates.";
    }

    @Override
    public String getCategory() {
        return "CONFORMAL BASELINE";
    }

    @Override
    public double getCurrentStepSize() {
        return stepSize;
    }
}
