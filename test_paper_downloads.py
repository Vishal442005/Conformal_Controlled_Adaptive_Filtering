import requests
import json

test_urls = [
    ("Paper 1 (Yoo 2026)", "https://arxiv.org/pdf/2501.14566.pdf", "https://doi.org/10.1109/TSP.2026.3650912"),
    ("Paper 2 (Lari 2026)", "https://arxiv.org/pdf/2602.18396.pdf", "https://ieeexplore.ieee.org/document/10902518"),
    ("Paper 3 (Zhu 2024)", "https://arxiv.org/pdf/2308.04237.pdf", "https://doi.org/10.1109/TSP.2024.3364964"),
    ("Paper 4 (Peng/Ghosh 2026)", "https://arxiv.org/pdf/2405.18417.pdf", "https://doi.org/10.1109/TSP.2026.3653790"),
    ("Paper 5 (Ghosh 2026 Saturation)", "https://www.researchgate.net/publication/393282247", "https://doi.org/10.1109/TSP.2026.3653790"),
    ("Paper 6 (Zhang 2024 NKF AEC)", "https://arxiv.org/pdf/2501.16367.pdf", "https://doi.org/10.1109/MSP.2024.3444062"),
    ("Paper 7 (Wang 2024 AEC Hybrid)", "https://arxiv.org/pdf/2410.09655.pdf", "https://doi.org/10.21437/Interspeech.2024")
]

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

for name, pdf_url, ieee_url in test_urls:
    try:
        r = requests.get(pdf_url, headers=headers, timeout=10, stream=True)
        content_type = r.headers.get("content-type", "")
        cl = r.headers.get("content-length", "0")
        is_pdf = "application/pdf" in content_type or (r.status_code == 200 and int(cl) > 50000)
        print(f"{name:<30}: Status={r.status_code} | Is_PDF={is_pdf} | Content-Type={content_type[:25]}")
    except Exception as e:
        print(f"{name:<30}: Error={e}")
