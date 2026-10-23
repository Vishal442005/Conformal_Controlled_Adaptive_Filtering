import os
import requests

downloads = [
    {
        "filename": "6_A_Fast_Robust_Adaptive_Filter_Using_Improved_Data_Reuse_IEEE_TSP_2026.pdf",
        "title": "A Fast Robust Adaptive Filter Using Improved Data-Reuse Method",
        "url": "https://arxiv.org/pdf/2405.18417.pdf"
    },
    {
        "filename": "7_Lightweight_Hybrid_Framework_AEC_Constrained_Recursive_Training_2024.pdf",
        "title": "A Lightweight Hybrid Framework for Acoustic Echo Cancellation and Suppression via Constrained Recursive Training",
        "url": "https://arxiv.org/pdf/2410.09655.pdf"
    }
]

out_dir = os.path.abspath("downloaded_papers")
os.makedirs(out_dir, exist_ok=True)
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

print("=" * 80)
print("DOWNLOADING REMAINING PAPERS FROM CATEGORIES 1 & 2")
print("=" * 80)

for d in downloads:
    dst = os.path.join(out_dir, d["filename"])
    print(f"\nDownloading: {d['title']}")
    print(f"  URL -> {d['url']}")
    try:
        r = requests.get(d["url"], headers=headers, timeout=30)
        if r.status_code == 200 and len(r.content) > 10000:
            with open(dst, "wb") as f:
                f.write(r.content)
            size_kb = len(r.content) / 1024.0
            print(f"  [SUCCESS] Saved ({size_kb:.1f} KB) -> {dst}")
        else:
            print(f"  [ERROR] Status {r.status_code}, Length {len(r.content)}")
    except Exception as e:
        print(f"  [ERROR] {e}")

print("\n" + "=" * 80)
