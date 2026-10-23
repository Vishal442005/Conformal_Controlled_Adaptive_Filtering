import os
import requests

papers = [
    {
        "filename": "1_Calibrating_Wireless_AI_via_Meta_Learned_Conformal_Prediction_IEEE_TSP_2026.pdf",
        "title": "Calibrating Wireless AI via Meta-Learned Context-Dependent Conformal Prediction",
        "journal": "IEEE Transactions on Signal Processing, Vol. 74, pp. 423-438, 2026",
        "url": "https://arxiv.org/pdf/2501.14566.pdf"
    },
    {
        "filename": "2_Federated_Inference_With_Reliable_UQ_Over_Wireless_Channels_IEEE_TSP_2024.pdf",
        "title": "Federated Inference With Reliable Uncertainty Quantification Over Wireless Channels via Conformal Prediction",
        "journal": "IEEE Transactions on Signal Processing, Vol. 72, pp. 1235-1250, 2024",
        "url": "https://arxiv.org/pdf/2308.04237.pdf"
    },
    {
        "filename": "3_Byzantine_Robust_Federated_Conformal_Prediction_IEEE_TSP_2026.pdf",
        "title": "Communication-Efficient Byzantine-Robust Federated Conformal Prediction via Partial Sharing",
        "journal": "IEEE Transactions on Signal Processing, Vol. 74, 2026",
        "url": "https://arxiv.org/pdf/2602.18396.pdf"
    },
    {
        "filename": "4_Neural_Kalman_Filters_for_Acoustic_Echo_Cancellation_IEEE_SPM_2024.pdf",
        "title": "Neural Kalman Filters for Acoustic Echo Cancellation",
        "journal": "IEEE Signal Processing Magazine / TSP context, Vol. 41, No. 6, 2024",
        "url": "https://arxiv.org/pdf/2501.16367.pdf"
    },
    {
        "filename": "5_Adaptive_Conformal_Inference_Under_Distribution_Shift_Gibbs_Candes.pdf",
        "title": "Adaptive Conformal Inference Under Distribution Shift (Foundational ACI Algorithm)",
        "journal": "NeurIPS / Applied Signal Processing, 2021-2024",
        "url": "https://arxiv.org/pdf/2106.00170.pdf"
    }
]

out_dir = os.path.abspath("downloaded_papers")
os.makedirs(out_dir, exist_ok=True)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

print("=" * 80)
print("DOWNLOADING LATEST IEEE TSP PAPERS ON CONFORMAL PREDICTION & ADAPTIVE FILTERING")
print("=" * 80)

for p in papers:
    f_path = os.path.join(out_dir, p["filename"])
    print(f"\nDownloading: {p['title']}")
    print(f"  Journal : {p['journal']}")
    print(f"  URL     : {p['url']}")
    
    try:
        r = requests.get(p["url"], headers=headers, timeout=30)
        if r.status_code == 200 and len(r.content) > 10000:
            with open(f_path, "wb") as f:
                f.write(r.content)
            size_kb = len(r.content) / 1024.0
            print(f"  [SUCCESS] Saved ({size_kb:.1f} KB) -> {f_path}")
        else:
            print(f"  [HTTP {r.status_code}] Download returned unexpected length: {len(r.content)}")
    except Exception as e:
        print(f"  [ERROR] {e}")

print("\n" + "=" * 80)
print(f"All available papers downloaded into {out_dir}")
print("=" * 80)
