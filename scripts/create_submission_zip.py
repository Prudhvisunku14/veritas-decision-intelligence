#!/usr/bin/env python3
"""Script to package the Veritas KPI submission into a clean ZIP archive with SHA256 checksum."""

import os
import hashlib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_ZIP = ROOT / "Veritas_KPI_Round2_Submission.zip"

EXCLUDE_DIRS = {".git", ".venv", "__pycache__", ".pytest_cache", ".antigravity", ".vscode", "artifacts", "scratch"}
EXCLUDE_EXTS = {".pyc", ".pyo", ".pyd", ".zip"}

def create_zip():
    print(f"Creating submission package at {OUTPUT_ZIP}...")
    
    with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED) as zipf:
        for path in ROOT.rglob("*"):
            if path == OUTPUT_ZIP:
                continue
            
            # Check directory exclusions
            parts = path.relative_to(ROOT).parts
            if any(p in EXCLUDE_DIRS for p in parts):
                continue
            
            if path.is_file():
                if path.suffix in EXCLUDE_EXTS:
                    continue
                arcname = str(path.relative_to(ROOT))
                zipf.write(path, arcname)
                
    # Calculate SHA256 checksum
    hasher = hashlib.sha256()
    with open(OUTPUT_ZIP, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
            
    sha256_hash = hasher.hexdigest()
    print(f"ZIP created successfully!")
    print(f"File Path: {OUTPUT_ZIP}")
    print(f"Size: {OUTPUT_ZIP.stat().st_size / (1024*1024):.2f} MB")
    print(f"SHA256: {sha256_hash}")

    checksum_file = ROOT / "Veritas_KPI_Round2_Submission.zip.sha256"
    with open(checksum_file, "w") as f:
        f.write(f"{sha256_hash}  Veritas_KPI_Round2_Submission.zip\n")

if __name__ == "__main__":
    create_zip()
