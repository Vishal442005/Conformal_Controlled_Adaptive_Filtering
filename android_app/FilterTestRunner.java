import com.research.ccaf.dsp.*;

public class FilterTestRunner {
    public static void main(String[] args) {
        System.out.println("=== Testing CCAF DSP Algorithms in Java ===");

        AdaptiveFilter[] filters = new AdaptiveFilter[]{
                new CCAFDeadBandFilter(),
                new DecoupledACIFilter(),
                NLMSFilter.createFast(),
                NLMSFilter.createSlow(),
                new KwongVSSFilter(),
                new BenestyVSSFilter(),
                new ConvexCombinationFilter()
        };

        // Synthesize 500 samples of noisy speech/tone
        int N = 500;
        double[] testSignal = new double[N];
        for (int i = 0; i < N; i++) {
            double clean = 0.5 * Math.sin(2.0 * Math.PI * 440.0 * i / 16000.0);
            double noise = 0.1 * (Math.random() - 0.5);
            testSignal[i] = clean + noise;
        }

        for (AdaptiveFilter filter : filters) {
            filter.reset();
            AdaptiveFilter.Output lastOut = null;
            for (int i = 0; i < N; i++) {
                lastOut = filter.process(testSignal[i]);
            }
            System.out.printf("%-24s | Final mu: %.4f | Coverage: %5.1f%% | Winkler: %.3f%n",
                    filter.getName(),
                    filter.getCurrentStepSize(),
                    filter.getEmpiricalCoverage(),
                    filter.getWinklerScore());
        }

        System.out.println("=== All DSP Filters Executed Successfully! ===");
    }
}
