package com.research.ccaf.dsp;

/**
 * Proposed Conformal-Controlled Adaptive Filter with Dead-Band Step-Size Control (CCAF-DB).
 * Features finite-sample distribution-free prediction intervals and miscoverage feedback.
 */
public class CCAFDeadBandFilter extends AbstractAdaptiveFilter {

    private final double muMin;
    private final double muMax;
    private final double gamma;
    private final double alpha;
    private final double tauDeadBand;
    private final double kappaGain;
    private final double regDelta;

    private double currentStepSize;
    private double conformalQuantile;
    private double empiricalErrorRate;
    private final double errorRateSmoothing;

    public CCAFDeadBandFilter(int tapLength, double muMin, double muMax,
                              double gamma, double alpha, double tauDeadBand, double kappaGain) {
        super(tapLength);
        this.muMin = muMin;
        this.muMax = muMax;
        this.gamma = gamma;
        this.alpha = alpha;
        this.tauDeadBand = tauDeadBand;
        this.kappaGain = kappaGain;
        this.regDelta = 1e-4;

        this.currentStepSize = muMin;
        this.conformalQuantile = 1.645; // Initial quantile
        this.empiricalErrorRate = alpha;
        this.errorRateSmoothing = 0.98;
    }

    public CCAFDeadBandFilter() {
        this(64, 0.05, 0.50, 0.005, 0.10, 0.04, 8.0);
    }

    @Override
    public Output process(double inputSample) {
        // Desired target is the incoming sample
        double desired = inputSample;

        // In acoustic/audio cancellation setup, regressor is delayed input (line enhancer / predictor)
        // or synthetic reference. Using 1-sample decorrelation delay:
        int delayIdx = (bufferIndex - 1 + tapLength) % tapLength;
        double x_ref = regressorBuffer[delayIdx];

        // 1. Point prediction: y_hat(n) = w(n)^T x(n)
        double estimated = computeInnerProduct();

        // 2. Residual error: e(n) = d(n) - y_hat(n)
        double error = desired - estimated;

        // 3. Local dispersion scale s(n) = sqrt(runningVariance + eps)
        runningVariance = varianceSmoothing * runningVariance + (1.0 - varianceSmoothing) * (error * error);
        double scale = Math.sqrt(runningVariance + 1e-8);

        // 4. Normalized nonconformity score E(n) = |e(n)| / s(n)
        double score = Math.abs(error) / scale;

        // 5. Miscoverage indicator m(n) = I{E(n) > q(n)}
        boolean isMiss = (score > conformalQuantile);
        double missIndicator = isMiss ? 1.0 : 0.0;

        // 6. Online ACI quantile recursion: q(n+1) = q(n) + gamma * (alpha - m(n))
        conformalQuantile = Math.max(0.1, conformalQuantile + gamma * (alpha - missIndicator));

        // 7. Track empirical error rate
        empiricalErrorRate = errorRateSmoothing * empiricalErrorRate + (1.0 - errorRateSmoothing) * missIndicator;

        // 8. Dead-band conformal deficit controller
        double rawDeficit = empiricalErrorRate - alpha;
        double deadbandDeficit = Math.max(0.0, rawDeficit - tauDeadBand);

        // Step-size modulation: mu(n) = mu_min + (mu_max - mu_min) * min(1, kappa * c_DB)
        double controlAdjustment = Math.min(1.0, kappaGain * deadbandDeficit);
        currentStepSize = muMin + (muMax - muMin) * controlAdjustment;

        // 9. Normalized gradient weight update
        double energy = computeRegressorEnergy() + regDelta;
        double normalizedStep = currentStepSize / energy;
        int idx = bufferIndex;
        for (int i = 0; i < tapLength; i++) {
            idx = (idx - 1 + tapLength) % tapLength;
            weights[i] += normalizedStep * error * regressorBuffer[idx];
        }

        // Push new sample to delay line
        pushRegressorSample(desired);

        // 10. Compute conformal prediction bounds
        double halfWidth = conformalQuantile * scale;
        double lowerBound = estimated - halfWidth;
        double upperBound = estimated + halfWidth;

        // Update benchmark statistics
        updateStatistics(desired, lowerBound, upperBound, alpha);

        return new Output(desired, estimated, error, lowerBound, upperBound, currentStepSize, isMiss);
    }

    @Override
    public void reset() {
        super.reset();
        this.currentStepSize = muMin;
        this.conformalQuantile = 1.645;
        this.empiricalErrorRate = alpha;
    }

    @Override
    public String getName() {
        return "Proposed CCAF-DB";
    }

    @Override
    public String getDescription() {
        return "Conformal-Controlled Adaptive Filter with Dead-Band Step-Size Control. Combines distribution-free prediction bounds with nonconformity feedback for rapid tracking.";
    }

    @Override
    public String getCategory() {
        return "PROPOSED (RESEARCH)";
    }

    @Override
    public double getCurrentStepSize() {
        return currentStepSize;
    }
}
