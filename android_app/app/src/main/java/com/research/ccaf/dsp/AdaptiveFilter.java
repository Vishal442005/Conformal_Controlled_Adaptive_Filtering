package com.research.ccaf.dsp;

/**
 * Common interface for all adaptive filters in the CCAF research suite.
 */
public interface AdaptiveFilter {

    /**
     * Structure holding instantaneous sample outputs from the filter.
     */
    class Output {
        public final double desired;      // Raw original input y(n)
        public final double estimated;    // Filter prediction y_hat(n)
        public final double error;        // Cleaned/filtered error e(n) = y(n) - y_hat(n)
        public final double lowerBound;   // Confidence lower bound L(n)
        public final double upperBound;   // Confidence upper bound U(n)
        public final double stepSize;     // Current step-size mu(n)
        public final boolean isMiss;      // Conformal coverage miss indicator

        public Output(double desired, double estimated, double error,
                      double lowerBound, double upperBound, double stepSize, boolean isMiss) {
            this.desired = desired;
            this.estimated = estimated;
            this.error = error;
            this.lowerBound = lowerBound;
            this.upperBound = upperBound;
            this.stepSize = stepSize;
            this.isMiss = isMiss;
        }
    }

    /**
     * Process a single audio sample.
     * In an adaptive noise cancellation setup, a delayed version of the signal or a reference
     * serves as regressor x(n), and the noisy microphone sample serves as desired d(n).
     *
     * @param inputSample Raw audio input sample normalized to [-1.0, 1.0]
     * @return Output containing raw, estimated, cleaned error, and uncertainty bounds.
     */
    Output process(double inputSample);

    /**
     * Process full frame of normalized audio samples.
     */
    Output[] processFrame(double[] inputSamples);

    /**
     * Reset filter weights and internal states to initial conditions.
     */
    void reset();

    /**
     * Filter display name.
     */
    String getName();

    /**
     * Description and mathematical mechanism.
     */
    String getDescription();

    /**
     * Algorithmic family tag (e.g. "PROPOSED", "CONFORMAL", "VSS", "BASELINE").
     */
    String getCategory();

    /**
     * Current step size.
     */
    double getCurrentStepSize();

    /**
     * Running empirical coverage percentage [0, 100].
     */
    double getEmpiricalCoverage();

    /**
     * Running interval sharpness (Winkler score).
     */
    double getWinklerScore();
}
