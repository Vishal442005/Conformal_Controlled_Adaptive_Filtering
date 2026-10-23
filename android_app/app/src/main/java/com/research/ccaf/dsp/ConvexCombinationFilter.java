package com.research.ccaf.dsp;

/**
 * Convex Combination of Two Adaptive Filters (Arenas-Garcia et al.).
 * Mixes a fast filter (mu=0.50) and a slow filter (mu=0.05) via a sigmoidal parameter.
 */
public class ConvexCombinationFilter implements AdaptiveFilter {

    private final NLMSFilter fastFilter;
    private final NLMSFilter slowFilter;
    private final double muA;
    private double mixingA = 0.0; // Sigmoid activation parameter
    private double currentLambda = 0.5;

    public ConvexCombinationFilter(int tapLength, double muFast, double muSlow, double muA) {
        this.fastFilter = new NLMSFilter(tapLength, muFast, true);
        this.slowFilter = new NLMSFilter(tapLength, muSlow, false);
        this.muA = muA;
    }

    public ConvexCombinationFilter() {
        this(64, 0.50, 0.05, 0.10);
    }

    @Override
    public Output process(double inputSample) {
        Output outFast = fastFilter.process(inputSample);
        Output outSlow = slowFilter.process(inputSample);

        // Sigmoidal combination factor: lambda(n) = 1 / (1 + exp(-a(n)))
        currentLambda = 1.0 / (1.0 + Math.exp(-Math.max(-10.0, Math.min(10.0, mixingA))));

        // Overall estimated output
        double estimated = currentLambda * outFast.estimated + (1.0 - currentLambda) * outSlow.estimated;
        double error = inputSample - estimated;

        // Adaptation of combination parameter a(n)
        double diff = outFast.estimated - outSlow.estimated;
        mixingA += muA * error * diff * currentLambda * (1.0 - currentLambda);
        mixingA = Math.max(-10.0, Math.min(10.0, mixingA));

        // Combined bounds
        double lowerBound = currentLambda * outFast.lowerBound + (1.0 - currentLambda) * outSlow.lowerBound;
        double upperBound = currentLambda * outFast.upperBound + (1.0 - currentLambda) * outSlow.upperBound;
        boolean isMiss = (inputSample < lowerBound || inputSample > upperBound);

        double effectiveStep = currentLambda * outFast.stepSize + (1.0 - currentLambda) * outSlow.stepSize;

        return new Output(inputSample, estimated, error, lowerBound, upperBound, effectiveStep, isMiss);
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
        fastFilter.reset();
        slowFilter.reset();
        mixingA = 0.0;
        currentLambda = 0.5;
    }

    @Override
    public String getName() {
        return "Convex Combination";
    }

    @Override
    public String getDescription() {
        return "Convex Combination of Fast and Slow NLMS filters. Continuously balances transient agility and steady-state precision via sigmoidal weighting.";
    }

    @Override
    public String getCategory() {
        return "COMBINATION BASELINE";
    }

    @Override
    public double getCurrentStepSize() {
        return currentLambda * fastFilter.getCurrentStepSize() + (1.0 - currentLambda) * slowFilter.getCurrentStepSize();
    }

    @Override
    public double getEmpiricalCoverage() {
        return (fastFilter.getEmpiricalCoverage() + slowFilter.getEmpiricalCoverage()) / 2.0;
    }

    @Override
    public double getWinklerScore() {
        return (fastFilter.getWinklerScore() + slowFilter.getWinklerScore()) / 2.0;
    }
}
