# Implementation Checklist: Conformal-Controlled Adaptive Filtering (CCAF)

Based on the research plan in `Adaptive_Filtering_Research_Plan.pdf`.

---

## Phase 0: Project Setup & Environment
- [x] Initialize clean Python virtual environment / repo structure (`src/`, `configs/`, `tests/`, `experiments/`, `notebooks/`, `docs/`).
- [x] Configure dependencies (`numpy`, `scipy`, `matplotlib`, `pandas`, `statsmodels`, `pytest`, `wfdb`, `requests`).
- [x] Setup reproducibility framework: global seeding mechanism, centralized experiment config schema (`yaml` or dataclasses).

---

## Phase 1: Baseline Algorithms & Core Modules (Days 8–10 / Weeks 3–5)
### 1.1 Oracle Baselines
- [x] **Wiener Filter** (optimal stationary filter with known $R$ and $p$).
- [x] **State-space Kalman Filter Oracle** (known observation noise $\sigma_v^2$ and state noise $\sigma_q^2$).

### 1.2 Classical Fixed-Parameter Adaptive Filters
- [x] **Standard LMS** (fixed $\mu$, stability limit $0 < \mu < 2/\lambda_{\max}$).
- [x] **Normalized LMS (NLMS)** ($\mu / (\epsilon + \|u(n)\|^2)$ with $0 < \mu < 2$).
- [x] **Sign-Error LMS**.
- [x] **Recursive Least Squares (RLS)** with forgetting factor $\lambda$ (e.g. 0.99, 0.999).
- [x] **Affine Projection Algorithm (APA)** ($K = 2, 4$).

### 1.3 Competitor Variable Step-Size (VSS) & Combination Filters
- [x] **Kwong-Johnston VSS-LMS** (1992).
- [x] **Nonparametric VSS-NLMS** (Benesty et al., 2006).
- [x] **Sigmoid / Error-Feedback VSS-NLMS**.
- [x] **Gradient-Adaptive Step Size LMS/NLMS**.
- [x] **Convex Combination of Fast + Slow NLMS** (Arenas-Garcia et al., 2006).
- [x] **Sage-Husa Adaptive Kalman Filter** (online estimation of noise covariances).

### 1.4 Baseline Uncertainty Quantification Methods
- [x] **Gaussian Prediction Intervals** from RLS / Kalman state covariance ($y \pm z_{1-\alpha/2} \hat{\sigma}$).
- [x] **Static Split-Conformal** calibration on fixed-window NLMS residuals.
- [x] **Decoupled ACI on NLMS**: Standard ACI tracking coverage with fixed step-size NLMS (key ablation baseline).

---

## Phase 2: CCAF Algorithm Implementation (Days 11–12 / Weeks 6–9)
- [x] **Running Scale Estimator**:
  - Implement $s(n)$ (e.g. exponentially weighted RMS of past a-priori errors $e(n)$).
- [x] **Conformal Prediction Interval Layer**:
  - Normalized score calculation: $r(n) = |e(n)| / s(n)$.
  - Calibration quantile calculation: $q(n) = \text{Quantile}_{1-\alpha_n}(\text{recent scores}) \times s(n)$.
  - Miss flag indicator: $m(n) = \mathbb{I}(r(n) > q(n))$.
  - Adaptive Conformal Inference (ACI) update recursion:
    $$\alpha_{n+1} = \alpha_n + \gamma (\alpha - m(n))$$
- [x] **Coverage-Driven Step-Size Controller**:
  - Control signal mapping: $c(n) = \text{clip}\left(\frac{\alpha - \alpha_n}{\alpha}, 0, 1\right)$.
  - Step size formula: $\mu(n) = \mu_{\min} + (\mu_{\max} - \mu_{\min}) \cdot c(n)^p$.
- [x] **Coupled NLMS Weight Update**:
  $$w(n+1) = w(n) + \frac{\mu(n) e(n) u(n)}{\epsilon + \|u(n)\|^2}$$
- [x] Unit tests verifying algorithm correctness and parameter invariants ($\mu(n) \in [\mu_{\min}, \mu_{\max}]$).

---

## Phase 3: Synthetic Simulation Suite (Scenarios S1–S6)
Run Monte Carlo experiments (300 paired runs per cell):
- [x] **S1: Stationary Gaussian, White Input**
  - $M = 32$ taps, $T = 20{,}000$, SNR $\in \{-5, 0, 5, 10, 15, 20, 30\}$ dB.
  - Verify C2 nominal efficiency (CCAF steady-state EMSE matches NLMS $\mu_{\min}$ and Kalman lower bound).
- [x] **S2: Stationary Gaussian, Coloured Input**
  - AR(1) input process with $\rho \in \{0.5, 0.9, 0.99\}$ (eigenvalue spread test).
- [x] **S3: Abrupt Plant Change (Tracking & Recovery)**
  - Weight flip/rescaling at $n = 8{,}000$ across parameter sweep $\Delta$.
  - Evaluate C3 detection delay and recovery rate.
  - **Ablation**: Coupled CCAF vs Decoupled ACI-NLMS.
- [x] **S4: Random-Walk Plant**
  - Continuous drift $\sigma_q^2$ swept across 3 orders of magnitude; benchmark vs Kalman.
- [x] **S5: Time-Varying Noise Variance**
  - Piecewise $\sigma_v^2$ step jumps ($5\times$ to $20\times$).
- [x] **S6: Non-Gaussian Stress & Outliers**
  - Student-$t$ noise ($\nu \in \{2.5, 3, 5\}$).
  - Gaussian-mixture outliers ($5\%$ to $10\%$, scale $10\times$), impulsive noise.
  - Evaluate C4 robustness: empirical coverage and interval score vs Gaussian intervals.

---

## Phase 4: Metrics & Statistical Evaluation Pipeline (Section 6)
- [x] **Performance Metrics Computation**:
  - Mean Squared Deviation (MSD) learning curve (dB): $10 \log_{10} \mathbb{E}[\|w_o(n) - w(n)\|^2]$.
  - Steady-state Excess MSE (EMSE).
  - Tracking recovery time (time to reach within 1 dB of steady-state floor after step change).
  - Empirical coverage: overall and sliding-window.
  - Average interval width and Winkler score ($\text{width} + \frac{2}{\alpha} \times \text{distance outside}$).
  - Computational complexity (FLOPs/iteration and execution runtime).
- [x] **Statistical Significance Tests**:
  - Paired Wilcoxon signed-rank test on per-run steady-state EMSE (with Cliff's delta / Cohen's $d$).
  - Holm-Bonferroni correction for multiple pairwise tests.
  - Friedman test + Nemenyi post-hoc (Critical Difference diagrams).
  - BCa bootstrap (10,000 resamples) for 95% confidence bands on learning curves.
  - Clopper-Pearson exact confidence intervals for empirical coverage.

---

## Phase 5: Real-World Data Validation (Scenario S7)
- [x] **Dataset 1: EEG Artifact Removal** (EEGdenoiseNet benchmark).
- [x] **Dataset 2: ECG Noise Cancellation** (MIT-BIH with Noise Stress Test Database).
- [x] **Dataset 3: Acoustic Echo Cancellation (AEC)** (Aachen Impulse Response Database - AIR 1.4).
- [x] Standardize preprocessing pipeline and publish fixed preprocessing scripts.

---

## Phase 6: Ablations, Paper Figures & Reproducibility Pack
- [x] **Ablation Studies**:
  - $\gamma$ (adaptation rate) and nominal target $\alpha$ sensitivity.
  - Control exponent $p$ and clipping bounds.
  - Coupled vs Decoupled ACI-NLMS.
  - Filter length mismatch ($M_{\text{filter}} \neq M_{\text{system}}$).
- [x] **One-command reproduction script** (`run_all.py` / `make reproduce`) generating all figures and tables.
- [x] Pre-registration and archive artifact packaging (Zenodo/OSF ready).
