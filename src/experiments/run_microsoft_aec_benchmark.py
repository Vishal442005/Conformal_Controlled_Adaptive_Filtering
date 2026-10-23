import os
import json
import numpy as np
import scipy.io.wavfile as wav
import scipy.signal as signal
import matplotlib.pyplot as plt

DATA_DIR = os.path.abspath("data/microsoft_aec")
RESULTS_DIR = os.path.abspath("results")
FIGURES_DIR = os.path.abspath("paper_latex/figures")

os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(FIGURES_DIR, exist_ok=True)

class FastNLMS:
    def __init__(self, M=256, mu=0.2, delta=1e-4):
        self.M = M
        self.mu = mu
        self.delta = delta
        
    def filter(self, x_pad, x_in, d_in):
        N = len(x_in)
        M = self.M
        w = np.zeros(M)
        y_out = np.zeros(N)
        e_out = np.zeros(N)
        mu_out = np.full(N, self.mu)
        scale_out = np.zeros(N)
        sigma2_e = 1e-4
        
        for n in range(N):
            xv = x_pad[n : n + M]
            y = np.dot(w, xv)
            e = d_in[n] - y
            
            sigma2_e = 0.99 * sigma2_e + 0.01 * (e ** 2)
            scale = np.sqrt(sigma2_e + 1e-8)
            
            norm_x = np.dot(xv, xv) + self.delta
            w += (self.mu / norm_x) * e * xv
            
            y_out[n] = y
            e_out[n] = e
            scale_out[n] = scale
            
        return y_out, e_out, mu_out, scale_out

class FastKwongVSS:
    def __init__(self, M=256, mu_min=0.01, mu_max=0.5, alpha_vss=0.97, gamma_vss=0.05, delta=1e-4):
        self.M = M
        self.mu_min = mu_min
        self.mu_max = mu_max
        self.alpha_vss = alpha_vss
        self.gamma_vss = gamma_vss
        self.delta = delta
        
    def filter(self, x_pad, x_in, d_in):
        N = len(x_in)
        M = self.M
        w = np.zeros(M)
        y_out = np.zeros(N)
        e_out = np.zeros(N)
        mu_out = np.zeros(N)
        scale_out = np.zeros(N)
        mu = self.mu_min
        sigma2_e = 1e-4
        
        for n in range(N):
            xv = x_pad[n : n + M]
            y = np.dot(w, xv)
            e = d_in[n] - y
            
            sigma2_e = 0.99 * sigma2_e + 0.01 * (e ** 2)
            scale = np.sqrt(sigma2_e + 1e-8)
            
            norm_x = np.dot(xv, xv) + self.delta
            w += (mu / norm_x) * e * xv
            
            mu = self.alpha_vss * mu + self.gamma_vss * (e ** 2)
            mu = np.clip(mu, self.mu_min, self.mu_max)
            
            y_out[n] = y
            e_out[n] = e
            mu_out[n] = mu
            scale_out[n] = scale
            
        return y_out, e_out, mu_out, scale_out

class FastBenestyVSS:
    def __init__(self, M=256, mu_min=0.01, mu_max=0.5, lambda_e=0.98, delta=1e-4):
        self.M = M
        self.mu_min = mu_min
        self.mu_max = mu_max
        self.lambda_e = lambda_e
        self.delta = delta
        
    def filter(self, x_pad, x_in, d_in):
        N = len(x_in)
        M = self.M
        w = np.zeros(M)
        y_out = np.zeros(N)
        e_out = np.zeros(N)
        mu_out = np.zeros(N)
        scale_out = np.zeros(N)
        sigma_e2 = 1e-2
        sigma_v2 = 1e-3
        mu = self.mu_min
        
        for n in range(N):
            xv = x_pad[n : n + M]
            y = np.dot(w, xv)
            e = d_in[n] - y
            
            sigma_e2 = self.lambda_e * sigma_e2 + (1.0 - self.lambda_e) * (e ** 2)
            if sigma_e2 < sigma_v2 * 1.5:
                sigma_v2 = 0.999 * sigma_v2 + 0.001 * sigma_e2
                
            factor = max(0.0, 1.0 - sigma_v2 / max(sigma_e2, 1e-7))
            mu = np.clip(self.mu_max * factor, self.mu_min, self.mu_max)
            
            norm_x = np.dot(xv, xv) + self.delta
            w += (mu / norm_x) * e * xv
            
            scale = np.sqrt(max(1e-8, sigma_e2))
            y_out[n] = y
            e_out[n] = e
            mu_out[n] = mu
            scale_out[n] = scale
            
        return y_out, e_out, mu_out, scale_out

class FastConvexCombination:
    def __init__(self, M=256, mu1=0.5, mu2=0.05, mu_a=0.1, delta=1e-4):
        self.M = M
        self.mu1 = mu1
        self.mu2 = mu2
        self.mu_a = mu_a
        self.delta = delta
        
    def filter(self, x_pad, x_in, d_in):
        N = len(x_in)
        M = self.M
        w1 = np.zeros(M)
        w2 = np.zeros(M)
        y_out = np.zeros(N)
        e_out = np.zeros(N)
        mu_out = np.zeros(N)
        scale_out = np.zeros(N)
        a = 0.0
        s2_1 = 1e-4
        s2_2 = 1e-4
        
        for n in range(N):
            lam = 1.0 / (1.0 + np.exp(-np.clip(a, -10.0, 10.0)))
            xv = x_pad[n : n + M]
            
            y1 = np.dot(w1, xv)
            e1 = d_in[n] - y1
            norm_x = np.dot(xv, xv) + self.delta
            w1 += (self.mu1 / norm_x) * e1 * xv
            s2_1 = 0.99 * s2_1 + 0.01 * (e1 ** 2)
            
            y2 = np.dot(w2, xv)
            e2 = d_in[n] - y2
            w2 += (self.mu2 / norm_x) * e2 * xv
            s2_2 = 0.99 * s2_2 + 0.01 * (e2 ** 2)
            
            y = lam * y1 + (1.0 - lam) * y2
            e = d_in[n] - y
            
            a += self.mu_a * e * (y1 - y2) * lam * (1.0 - lam)
            a = np.clip(a, -10.0, 10.0)
            
            scale = np.sqrt(lam * s2_1 + (1.0 - lam) * s2_2 + 1e-8)
            y_out[n] = y
            e_out[n] = e
            mu_out[n] = lam * self.mu1 + (1.0 - lam) * self.mu2
            scale_out[n] = scale
            
        return y_out, e_out, mu_out, scale_out

class FastDecoupledACI:
    def __init__(self, M=256, mu=0.05, gamma=0.005, alpha=0.10, delta=1e-4):
        self.M = M
        self.mu = mu
        self.gamma = gamma
        self.alpha = alpha
        self.delta = delta
        
    def filter(self, x_pad, x_in, d_in):
        N = len(x_in)
        M = self.M
        w = np.zeros(M)
        y_out = np.zeros(N)
        e_out = np.zeros(N)
        mu_out = np.full(N, self.mu)
        scale_out = np.zeros(N)
        q_out = np.zeros(N)
        q = 1.645
        sigma2_e = 1e-4
        
        for n in range(N):
            xv = x_pad[n : n + M]
            y = np.dot(w, xv)
            e = d_in[n] - y
            
            sigma2_e = 0.99 * sigma2_e + 0.01 * (e ** 2)
            scale = np.sqrt(sigma2_e + 1e-8)
            
            score = abs(e) / scale
            miss = 1.0 if score > q else 0.0
            # Correct ACI update: expand on miss, contract on hit
            q = max(0.5, min(6.0, q + self.gamma * (miss - self.alpha)))
            
            norm_x = np.dot(xv, xv) + self.delta
            w += (self.mu / norm_x) * e * xv
            
            y_out[n] = y
            e_out[n] = e
            scale_out[n] = scale
            q_out[n] = q
            
        return y_out, e_out, mu_out, scale_out, q_out

class FastCCAFDeadBand:
    def __init__(self, M=256, mu_min=0.05, mu_max=0.50, gamma=0.005, alpha=0.10, tau=0.04, kappa=8.0, delta=1e-4):
        self.M = M
        self.mu_min = mu_min
        self.mu_max = mu_max
        self.gamma = gamma
        self.alpha = alpha
        self.tau = tau
        self.kappa = kappa
        self.delta = delta
        
    def filter(self, x_pad, x_in, d_in):
        N = len(x_in)
        M = self.M
        w = np.zeros(M)
        y_out = np.zeros(N)
        e_out = np.zeros(N)
        mu_out = np.zeros(N)
        scale_out = np.zeros(N)
        q_out = np.zeros(N)
        q = 1.645
        err_rate = self.alpha
        sigma2_e = 1e-4
        mu = self.mu_min
        
        for n in range(N):
            xv = x_pad[n : n + M]
            y = np.dot(w, xv)
            e = d_in[n] - y
            
            sigma2_e = 0.99 * sigma2_e + 0.01 * (e ** 2)
            scale = np.sqrt(sigma2_e + 1e-8)
            
            score = abs(e) / scale
            miss = 1.0 if score > q else 0.0
            # Correct ACI update: expand on miss, contract on hit
            q = max(0.5, min(6.0, q + self.gamma * (miss - self.alpha)))
            
            err_rate = 0.98 * err_rate + 0.02 * miss
            raw_deficit = err_rate - self.alpha
            c_DB = max(0.0, raw_deficit - self.tau)
            mu = self.mu_min + (self.mu_max - self.mu_min) * min(1.0, self.kappa * c_DB)
            
            norm_x = np.dot(xv, xv) + self.delta
            w += (mu / norm_x) * e * xv
            
            y_out[n] = y
            e_out[n] = e
            mu_out[n] = mu
            scale_out[n] = scale
            q_out[n] = q
            
        return y_out, e_out, mu_out, scale_out, q_out

def align_signals_cross_correlation(x, d, max_search=32000):
    """Normalized cross-correlation bulk-delay estimation."""
    corr_win = min(len(x), len(d), max_search)
    corr = signal.correlate(d[:corr_win], x[:corr_win], mode="full")
    lags = signal.correlation_lags(corr_win, corr_win, mode="full")
    lag = lags[np.argmax(corr)]
    
    if lag > 0:
        x_al = np.pad(x, (lag, 0))[:len(d)]
        d_al = d
    elif lag < 0:
        x_al = x[-lag:]
        d_al = d[:len(x_al)]
    else:
        x_al = x
        d_al = d
    return x_al, d_al, lag

def compute_erle_curve(d, e, window=512):
    N = len(d)
    erle = np.zeros(N)
    d2 = d ** 2
    e2 = e ** 2
    cumsum_d2 = np.cumsum(d2)
    cumsum_e2 = np.cumsum(e2)
    
    for i in range(N):
        if i < window:
            pd = cumsum_d2[i] / (i + 1)
            pe = cumsum_e2[i] / (i + 1)
        else:
            pd = (cumsum_d2[i] - cumsum_d2[i - window]) / window
            pe = (cumsum_e2[i] - cumsum_e2[i - window]) / window
        erle[i] = 10.0 * np.log10(max(1e-7, pd) / max(1e-7, pe))
    return erle

def compute_metrics(d, e, scale, q, alpha=0.10):
    N = len(d)
    half_width = q * scale
    hits = np.sum(np.abs(e) <= half_width)
    cov = (hits / N) * 100.0
    
    viol = np.maximum(0.0, np.abs(e) - half_width)
    winkler = np.mean(2.0 * half_width + (2.0 / alpha) * viol)
    
    start_ss = int(N * 0.5)
    pd_ss = np.mean(d[start_ss:] ** 2)
    pe_ss = np.mean(e[start_ss:] ** 2)
    erle_ss = 10.0 * np.log10(max(1e-7, pd_ss) / max(1e-7, pe_ss))
    
    return cov, winkler, erle_ss

def main():
    print("=== Running Aligned Microsoft Interspeech AEC Challenge Benchmark ===")
    
    files = sorted(os.listdir(DATA_DIR))
    
    pairs_by_cat = {
        "farend_singletalk": [],
        "farend_singletalk_with_movement": [],
        "doubletalk": [],
        "doubletalk_with_movement": []
    }
    
    for f in files:
        if not f.endswith("_lpb.wav"):
            continue
        prefix = f.replace("_lpb.wav", "")
        mic = f"{prefix}_mic_c.wav"
        if mic not in files:
            continue
            
        lpb_p = os.path.join(DATA_DIR, f)
        mic_p = os.path.join(DATA_DIR, mic)
        
        if "farend_singletalk_with_movement" in f:
            pairs_by_cat["farend_singletalk_with_movement"].append((lpb_p, mic_p))
        elif "farend_singletalk" in f:
            pairs_by_cat["farend_singletalk"].append((lpb_p, mic_p))
        elif "doubletalk_with_movement" in f:
            pairs_by_cat["doubletalk_with_movement"].append((lpb_p, mic_p))
        elif "doubletalk" in f:
            pairs_by_cat["doubletalk"].append((lpb_p, mic_p))
            
    algorithms = [
        "NLMS (fast)",
        "NLMS (slow)",
        "Kwong VSS-LMS",
        "Benesty NP-VSS",
        "Convex Combination",
        "Decoupled ACI",
        "Proposed CCAF-DB"
    ]
    
    results = {
        "scenario_erle": {alg: {} for alg in algorithms},
        "scenario_winkler": {alg: {} for alg in algorithms},
        "scenario_coverage": {alg: {} for alg in algorithms},
        "tracking_delay_ms": {alg: 0.0 for alg in algorithms}
    }
    
    sample_trajectories = {}
    M = 256
    
    for cat, pairs in pairs_by_cat.items():
        print(f"\nEvaluating Category: {cat} ({len(pairs)} pairs)...")
        cat_metrics = {alg: {"erle": [], "winkler": [], "coverage": []} for alg in algorithms}
        
        for lpb_path, mic_path in pairs:
            sr, x = wav.read(lpb_path)
            sr2, d = wav.read(mic_path)
            
            x = x.astype(np.float64) / 32768.0
            d = d.astype(np.float64) / 32768.0
            
            # STAGE 1: Standard Bulk Delay Alignment
            x_al, d_al, lag = align_signals_cross_correlation(x, d)
            
            # STAGE 2: Adaptive Filtering over Aligned Signals
            min_len = min(len(x_al), len(d_al))
            x_al, d_al = x_al[:min_len], d_al[:min_len]
            x_pad = np.pad(x_al, (M - 1, 0))
            
            filter_instances = {
                "NLMS (fast)": FastNLMS(M=M, mu=0.50),
                "NLMS (slow)": FastNLMS(M=M, mu=0.05),
                "Kwong VSS-LMS": FastKwongVSS(M=M),
                "Benesty NP-VSS": FastBenestyVSS(M=M),
                "Convex Combination": FastConvexCombination(M=M),
                "Decoupled ACI": FastDecoupledACI(M=M),
                "Proposed CCAF-DB": FastCCAFDeadBand(M=M)
            }
            
            for alg_name, flt in filter_instances.items():
                if alg_name in ["Decoupled ACI", "Proposed CCAF-DB"]:
                    y, e, mu, scale, q = flt.filter(x_pad, x_al, d_al)
                else:
                    y, e, mu, scale = flt.filter(x_pad, x_al, d_al)
                    q = np.full_like(scale, 1.645)
                    
                cov, wink, erle_ss = compute_metrics(d_al, e, scale, q)
                cat_metrics[alg_name]["erle"].append(erle_ss)
                cat_metrics[alg_name]["winkler"].append(wink)
                cat_metrics[alg_name]["coverage"].append(cov)
                
                if cat == "farend_singletalk_with_movement" and alg_name not in sample_trajectories:
                    sample_trajectories[alg_name] = compute_erle_curve(d_al, e, window=512)
                    
        for alg_name in algorithms:
            results["scenario_erle"][alg_name][cat] = float(np.mean(cat_metrics[alg_name]["erle"]))
            results["scenario_winkler"][alg_name][cat] = float(np.mean(cat_metrics[alg_name]["winkler"]))
            results["scenario_coverage"][alg_name][cat] = float(np.mean(cat_metrics[alg_name]["coverage"]))
            
    # Compute Tracking Recovery Delay in ms under movement
    fs = 16000
    for alg_name, erle_curve in sample_trajectories.items():
        # Midpoint is movement perturbation
        mid = len(erle_curve) // 2
        post = erle_curve[mid:]
        peak_ss = np.percentile(post, 80)
        target_re = max(2.0, peak_ss * 0.70)
        recov_idx = np.where(post >= target_re)[0]
        delay_spl = recov_idx[0] if len(recov_idx) > 0 else len(post)
        results["tracking_delay_ms"][alg_name] = float((delay_spl / fs) * 1000.0)
        
    print("\n" + "=" * 98)
    print(f"{'Algorithm':<20} | {'Single-Talk':<12} | {'Moving Far-End':<14} | {'Double-Talk':<12} | {'Delay (ms)':<10} | {'Coverage':<8}")
    print("-" * 98)
    for alg in algorithms:
        st = results["scenario_erle"][alg]["farend_singletalk"]
        mv = results["scenario_erle"][alg]["farend_singletalk_with_movement"]
        dt = results["scenario_erle"][alg]["doubletalk"]
        del_ms = results["tracking_delay_ms"][alg]
        cov = results["scenario_coverage"][alg]["farend_singletalk"]
        print(f"{alg:<20} | {st:8.2f} dB   | {mv:8.2f} dB     | {dt:8.2f} dB   | {del_ms:6.1f} ms  | {cov:5.1f}%")
    print("=" * 98)
    
    out_json = os.path.join(RESULTS_DIR, "microsoft_aec_benchmark_results.json")
    with open(out_json, "w") as f:
        json.dump(results, f, indent=2)
    print("Saved JSON results to:", out_json)
    
    generate_publication_figure(results, sample_trajectories)

def generate_publication_figure(results, sample_trajectories):
    algorithms = [
        "NLMS (fast)",
        "NLMS (slow)",
        "Kwong VSS-LMS",
        "Benesty NP-VSS",
        "Convex Combination",
        "Decoupled ACI",
        "Proposed CCAF-DB"
    ]
    colors = {
        "NLMS (fast)": "#94a3b8",
        "NLMS (slow)": "#64748b",
        "Kwong VSS-LMS": "#d97706",
        "Benesty NP-VSS": "#0284c7",
        "Convex Combination": "#8b5cf6",
        "Decoupled ACI": "#f59e0b",
        "Proposed CCAF-DB": "#10b981"
    }
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    plt.subplots_adjust(hspace=0.28, wspace=0.25)
    
    # (a) Bar chart of ERLE across all scenarios
    ax = axes[0, 0]
    scenarios = [
        ("farend_singletalk", "Single-Talk"),
        ("farend_singletalk_with_movement", "Moving Far-End"),
        ("doubletalk", "Double-Talk"),
        ("doubletalk_with_movement", "Moving DT")
    ]
    x = np.arange(len(scenarios))
    bw = 0.11
    for i, alg in enumerate(algorithms):
        vals = [results["scenario_erle"][alg][s[0]] for s in scenarios]
        offset = (i - 3) * bw
        ax.bar(x + offset, vals, bw, label=alg, color=colors[alg],
               edgecolor="black" if alg == "Proposed CCAF-DB" else "none",
               linewidth=1.2 if alg == "Proposed CCAF-DB" else 0)
        
    ax.set_xticks(x)
    ax.set_xticklabels([s[1] for s in scenarios], fontsize=11, fontweight="bold")
    ax.set_ylabel("Echo Return Loss Enhancement (ERLE) [dB]", fontsize=11)
    ax.set_title("(a) Microsoft AEC Challenge: ERLE Across Real Environments", fontsize=12, fontweight="bold")
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(fontsize=8, loc="upper right")
    
    # (b) Re-convergence trajectory under moving talker
    ax = axes[0, 1]
    fs = 16000
    for alg in ["NLMS (slow)", "Kwong VSS-LMS", "Benesty NP-VSS", "Decoupled ACI", "Proposed CCAF-DB"]:
        if alg in sample_trajectories:
            curve = sample_trajectories[alg]
            time_sec = np.arange(len(curve)) / fs
            step = 64
            lw = 2.5 if alg == "Proposed CCAF-DB" else 1.5
            ls = "-" if alg == "Proposed CCAF-DB" else "--"
            ax.plot(time_sec[::step], curve[::step], label=alg, color=colors[alg], linewidth=lw, linestyle=ls)
            
    ax.set_xlabel("Time [seconds]", fontsize=11)
    ax.set_ylabel("Instantaneous ERLE [dB]", fontsize=11)
    ax.set_title("(b) Acoustic Movement Event: Re-convergence Trajectory", fontsize=12, fontweight="bold")
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(fontsize=8.5, loc="lower right")
    
    # (c) Horizontal bar chart of delay
    ax = axes[1, 0]
    delays = [results["tracking_delay_ms"][alg] for alg in algorithms]
    y = np.arange(len(algorithms))
    bars = ax.barh(y, delays, color=[colors[a] for a in algorithms], height=0.6)
    bars[-1].set_edgecolor("black")
    bars[-1].set_linewidth(1.5)
    
    for i, d in enumerate(delays):
        ax.text(d + 4, i, f"{d:.1f} ms", va="center", fontsize=9, fontweight="bold")
        
    ax.set_yticks(y)
    ax.set_yticklabels(algorithms, fontsize=10)
    ax.set_xlabel("Re-adaptation Delay [ms] (Lower is Better)", fontsize=11)
    ax.set_title("(c) Tracking Recovery Delay Under Speaker Movement", fontsize=12, fontweight="bold")
    ax.grid(True, linestyle="--", alpha=0.5, axis="x")
    
    # (d) Winkler Sharpness vs Empirical Coverage
    ax = axes[1, 1]
    for alg in algorithms:
        cov = results["scenario_coverage"][alg]["farend_singletalk"]
        wink = results["scenario_winkler"][alg]["farend_singletalk"]
        marker = "*" if alg == "Proposed CCAF-DB" else "o"
        size = 220 if alg == "Proposed CCAF-DB" else 100
        ax.scatter(cov, wink, color=colors[alg], s=size, marker=marker, label=alg, edgecolors="black", zorder=5)
        ax.annotate(alg, (cov, wink), textcoords="offset points", xytext=(8, 4), fontsize=8.5,
                    fontweight="bold" if "Proposed" in alg else "normal")
        
    ax.axvline(90.0, color="#ef4444", linestyle=":", linewidth=1.8, label="Nominal Target (90%)")
    ax.set_xlabel("Empirical Coverage [%] (Target = 90%)", fontsize=11)
    ax.set_ylabel("Interval Sharpness (Winkler Score) [Lower is Better]", fontsize=11)
    ax.set_title("(d) Real Hardware Uncertainty Calibration & Sharpness", fontsize=12, fontweight="bold")
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(fontsize=8, loc="upper left")
    
    plt.tight_layout()
    out_fig = os.path.join(RESULTS_DIR, "microsoft_aec_benchmark.png")
    plt.savefig(out_fig, dpi=300)
    plt.savefig(os.path.join(FIGURES_DIR, "microsoft_aec_benchmark.png"), dpi=300)
    plt.close()
    print("Saved publication figure to:", out_fig)

if __name__ == "__main__":
    main()
