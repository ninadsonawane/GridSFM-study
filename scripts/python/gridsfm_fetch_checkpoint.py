"""Retrieve the pinned 61 MB Microsoft v1.1 file, verify SHA256 before load.

Not executed during the research package. Existing destination is never replaced.
"""
import argparse
import hashlib
from pathlib import Path
import urllib.request

REVISION = "1b41299b80252adf1869d5c3b479a4a402c52591"
SHA256 = "f8a4396122e603e8303afdebe3b093819c0f64dac0878394aed0bd63205fd831"
SIZE = 61061952
URL = f"https://huggingface.co/microsoft/GridSFM_Open/resolve/{REVISION}/gridsfm_open_v1.1.pt"


def main():
    p = argparse.ArgumentParser(description=__doc__); p.add_argument("destination", type=Path)
    dest = p.parse_args().destination
    if dest.exists(): raise FileExistsError(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    partial = dest.with_suffix(dest.suffix+".part")
    h, size = hashlib.sha256(), 0
    with urllib.request.urlopen(URL, timeout=120) as src, partial.open("xb") as dst:
        while True:
            chunk = src.read(1024*1024)
            if not chunk: break
            h.update(chunk); size += len(chunk); dst.write(chunk)
    if size != SIZE or h.hexdigest() != SHA256:
        raise ValueError("Checkpoint size/hash mismatch; .part retained for diagnosis")
    partial.rename(dest)
    print(f"Verified {size} bytes SHA256={h.hexdigest()} at {dest}")


if __name__ == "__main__": main()
