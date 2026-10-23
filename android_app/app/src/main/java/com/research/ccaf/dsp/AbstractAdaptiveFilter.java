package com.research.ccaf.dsp;

/**
 * Base abstract class handling circular delay line, inner products,
 * norm tracking, and conformal/coverage statistics.
 */
public abstract class AbstractAdaptiveFilter implements AdaptiveFilter {

    protected final int tapLength;
    protected final double[] weights;
    protected final double[] regressorBuffer;
    protected int bufferIndex = 0;

    // Running performance statistics
    protected long totalProcessedSamples = 0;
    protected long coverageHits = 0;
    protected double cumulativeWinklerScore = 0.0;
    protected double runningVariance = 1e-4;
    protected final double varianceSmoothing = 0.99;

    public AbstractAdaptiveFilter(int tapLength) {
        this.tapLength = tapLength;
        this.weights = new double[tapLength];
        this.regressorBuffer = new double[tapLength];
    }

    /**
     * Push a new sample into the regressor buffer.
     */
    protected void pushRegressorSample(double x) {
        regressorBuffer[bufferIndex] = x;
        bufferIndex = (bufferIndex + 1) % tapLength;
    }

    /**
     * Compute inner product w(n)^T x(n) using circular buffer.
     */
    protected double computeInnerProduct() {
        double sum = 0.0;
        int idx = bufferIndex;
        for (int i = 0; i < tapLength; i++) {
            idx = (idx - 1 + tapLength) % tapLength;
            sum += weights[i] * regressorBuffer[idx];
        }
        return sum;
    }

    /**
     * Compute squared Euclidean norm ||x(n)||^2.
     */
    protected double computeRegressorEnergy() {
        double energy = 0.0;
        for (int i = 0; i < tapLength; i++) {
            double val = regressorBuffer[i];
            energy += val * val;
        }
        return energy;
    }

    /**
     * Update running statistics: empirical coverage and Winkler score.
     */
    protected void updateStatistics(double desired, double lowerBound, double upperBound, double alpha) {
        totalProcessedSamples++;
        boolean hit = (desired >= lowerBound && desired <= upperBound);
        if (hit) {
            coverageHits++;
        }

        double width = upperBound - lowerBound;
        double penalty = 0.0;
        if (desired < lowerBound) {
            penalty = (2.0 / alpha) * (lowerBound - desired);
        } else if (desired > upperBound) {
            penalty = (2.0 / alpha) * (desired - upperBound);
        }
        cumulativeWinklerScore += (width + penalty);
    }

    @Override
    public Output[] processFrame(double[] inputSamples) {
        Output[] outputs = new Output[inputSamples.length];
        for (int i = 0; i < inputSamples.length; i++) {
            outputs[i] = process(inputSamples[i]);
        }
        return outputs;
    }

    @Override
    public void reset() {
        for (int i = 0; i < tapLength; i++) {
            weights[i] = 0.0;
            regressorBuffer[i] = 0.0;
        }
        bufferIndex = 0;
        totalProcessedSamples = 0;
        coverageHits = 0;
        cumulativeWinklerScore = 0.0;
        runningVariance = 1e-4;
    }

    @Override
    public double getEmpiricalCoverage() {
        if (totalProcessedSamples == 0) return 0.0;
        return (100.0 * coverageHits) / totalProcessedSamples;
    }

    @Override
    public double getWinklerScore() {
        if (totalProcessedSamples == 0) return 0.0;
        return cumulativeWinklerScore / totalProcessedSamples;
    }
}
