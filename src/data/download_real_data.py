import os
import wfdb
import requests

def download_nstdb_data():
    """
    Downloads PhysioNet MIT-BIH Noise Stress Test Database (NSTDB)
    and MIT-BIH Arrhythmia clean baseline record 118.
    """
    target_dir = os.path.abspath("data/ecg")
    os.makedirs(target_dir, exist_ok=True)
    print(f"Downloading PhysioNet NSTDB into {target_dir}...")

    # Download NSTDB noise records: bw (baseline wander), ma (muscle artifact), em (electrode motion)
    try:
        wfdb.dl_database("nstdb", dl_dir=target_dir, records=["bw", "ma", "em", "118e_6"])
        print("[SUCCESS] NSTDB downloaded.")
    except Exception as e:
        print(f"[WARNING] dl_database nstdb encountered: {e}")

    # Download clean MIT-BIH Arrhythmia baseline record 118
    try:
        wfdb.dl_database("mitdb", dl_dir=os.path.join(target_dir, "mitdb"), records=["118"])
        print("[SUCCESS] MIT-BIH record 118 downloaded.")
    except Exception as e:
        print(f"[WARNING] dl_database mitdb encountered: {e}")

def download_eeg_sample_data():
    """
    Downloads sample EEG data from the official EEGdenoiseNet repository for Scenario S7.
    """
    eeg_dir = os.path.abspath("data/eeg")
    os.makedirs(eeg_dir, exist_ok=True)
    print(f"Checking EEGdenoiseNet data in {eeg_dir}...")

    # Download sample epochs from the official repo release / raw GitHub
    base_url = "https://raw.githubusercontent.com/ncclabsustech/EEGdenoiseNet/master/data/"
    sample_files = ["EEG_all_epochs.npy", "EOG_all_epochs.npy"]

    for fname in sample_files:
        local_path = os.path.join(eeg_dir, fname)
        if not os.path.exists(local_path):
            url = base_url + fname
            print(f"Downloading {fname} from {url}...")
            try:
                r = requests.get(url, stream=True, timeout=15)
                if r.status_code == 200:
                    with open(local_path, "wb") as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                    print(f"[SUCCESS] Downloaded {fname}")
                else:
                    print(f"[NOTE] GitHub raw returned HTTP {r.status_code} (files may be tracked via Git LFS).")
            except Exception as ex:
                print(f"[NOTE] Could not stream {fname}: {ex}")

if __name__ == "__main__":
    download_nstdb_data()
    download_eeg_sample_data()
