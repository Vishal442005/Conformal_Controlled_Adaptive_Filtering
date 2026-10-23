import os
import json
import urllib.request
import re

DATA_DIR = "/media/jarvis/Imported/Research2/data/microsoft_aec"
POINTER_DIR = "/tmp/aec_repo/datasets/test_set/clean"

os.makedirs(DATA_DIR, exist_ok=True)

def parse_pointer_file(filepath):
    """Parse oid and size from git-lfs pointer file."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    oid_match = re.search(r"oid sha256:([0-9a-fA-F]+)", content)
    size_match = re.search(r"size (\d+)", content)
    if oid_match and size_match:
        return oid_match.group(1), int(size_match.group(1))
    return None, None

def get_download_urls(oid_size_list):
    """Batch request signed download URLs from GitHub LFS API."""
    url = "https://github.com/microsoft/AEC-Challenge.git/info/lfs/objects/batch"
    payload = {
        "operation": "download",
        "transfers": ["basic"],
        "objects": [{"oid": oid, "size": size} for oid, size in oid_size_list]
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "User-Agent": "git-lfs/3.0.0",
            "Accept": "application/vnd.git-lfs+json",
            "Content-Type": "application/vnd.git-lfs+json"
        }
    )
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode("utf-8"))
    
    url_map = {}
    for obj in res.get("objects", []):
        if "actions" in obj and "download" in obj["actions"]:
            url_map[obj["oid"]] = obj["actions"]["download"]["href"]
    return url_map

def download_file(url, target_path):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as resp, open(target_path, "wb") as out_file:
        out_file.write(resp.read())

def main():
    print("Collecting Microsoft AEC Challenge test files...")
    all_files = sorted(os.listdir(POINTER_DIR))
    
    categories = [
        "farend_singletalk",
        "farend_singletalk_with_movement",
        "doubletalk",
        "doubletalk_with_movement"
    ]
    
    target_files = []
    for cat in categories:
        cat_lpb = [f for f in all_files if f.endswith(f"{cat}_lpb.wav")]
        selected = cat_lpb[:5] # 5 representative paired trials per category (20 pairs = 40 audio files)
        for f in selected:
            prefix = f.replace("_lpb.wav", "")
            mic_f = f"{prefix}_mic_c.wav"
            target_files.append((f, cat))
            target_files.append((mic_f, cat))
            
    print(f"Total files selected for download: {len(target_files)}")
    
    # Parse pointer data
    oid_size_map = {}
    file_to_oid = {}
    for fname, cat in target_files:
        p_path = os.path.join(POINTER_DIR, fname)
        if os.path.exists(p_path):
            oid, size = parse_pointer_file(p_path)
            if oid and size:
                oid_size_map[oid] = size
                file_to_oid[fname] = oid
                
    print(f"Parsed {len(oid_size_map)} unique Git-LFS pointers. Requesting download URLs...")
    oid_size_list = [{"oid": oid, "size": size} for oid, size in oid_size_map.items()]
    url_map = get_download_urls([(x["oid"], x["size"]) for x in oid_size_list])
    
    print(f"Obtained {len(url_map)} signed download URLs. Downloading audio files...")
    for idx, (fname, cat) in enumerate(target_files, 1):
        target_path = os.path.join(DATA_DIR, fname)
        if os.path.exists(target_path) and os.path.getsize(target_path) > 1000:
            print(f"[{idx}/{len(target_files)}] Already exists: {fname}")
            continue
            
        oid = file_to_oid.get(fname)
        if oid in url_map:
            print(f"[{idx}/{len(target_files)}] Downloading: {fname}...")
            download_file(url_map[oid], target_path)
        else:
            print(f"Warning: No URL for {fname}")
            
    print("Download complete! Files saved to:", DATA_DIR)

if __name__ == "__main__":
    main()
