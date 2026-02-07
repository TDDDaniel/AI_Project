from fastapi import FastAPI, UploadFile, File
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware
import os
import json
import shutil
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],  # frontend-ul tău
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- FOLDER LIBRARY ---
LIBRARY = Path("data/library")
LIBRARY.mkdir(parents=True, exist_ok=True)

# --- UPLOAD ENDPOINT ---
@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    # Salvare fișier PDF în data/library
    path = LIBRARY / file.filename

    with open(path, "wb") as f:
        f.write(await file.read())

    return {"status": "uploaded", "file": file.filename}

METADATA_VERSION = "metadata-v9"

# --- SCANNER ---
def scan_library(library_path):
    """Returnează lista PDF-urilor din library."""
    files = []
    for root, _, filenames in os.walk(library_path):
        for f in filenames:
            if f.lower().endswith(".pdf"):
                files.append(os.path.join(root, f))
    print(f"[Scanner] Found {len(files)} PDF files")
    return files


# --- MATCHER (STABIL, FĂRĂ DEPENDENȚE) ---
def is_armv8_manual(pdf_path):
    filename = os.path.basename(pdf_path).lower()

    # 1️⃣ Detectare după nume (SAFE pentru demo)
    if "armv8" in filename and "armv9" not in filename:
        print(f"✅ Detected ARMv8 by filename: {pdf_path}")
        return True

    # 2️⃣ Detectare fallback: fișier text asociat (opțional)
    txt_version = pdf_path.replace(".pdf", ".txt")
    if os.path.exists(txt_version):
        with open(txt_version, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read().lower()
            if "armv8" in content:
                print(f"✅ Detected ARMv8 by content: {pdf_path}")
                return True

    print(f"❌ Not ARMv8: {pdf_path}")
    return False


def find_armv8_manual(files):
    for f in files:
        if is_armv8_manual(f):
            return f
    return None


# --- LINKER ---
def create_symlink(source, target_dir):
    os.makedirs(target_dir, exist_ok=True)

    target_path = os.path.join(target_dir, os.path.basename(source))

    if os.path.exists(target_path):
        print(f"[Linker] Already exists: {target_path}")
        return target_path

    try:
        os.symlink(source, target_path)
        print(f"[Linker] Symlink created: {target_path}")
    except OSError:
        # Fallback pentru Windows fără privilegii
        shutil.copy2(source, target_path)
        print(f"[Linker] Symlink not allowed → file copied instead")

    return target_path


# --- METADATA ---
def attach_metadata(file_path, version):
    metadata = {
        "metadata_version": version,
        "organized_by": "VirtualClawbot",
        "original_file": os.path.basename(file_path)
    }

    meta_path = file_path + ".meta.json"

    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print(f"[Metadata] Metadata attached: {meta_path}")
    return meta_path


# --- ORCHESTRATOR ---
def organize(library_path, clawbot_path):
    print("=== Virtual Clawbot Organizer START ===")

    files = scan_library(library_path)
    manual = find_armv8_manual(files)

    if not manual:
        print("❌ Manual ARMv8 nu a fost găsit")
        return {"status": "not_found"}

    link = create_symlink(manual, clawbot_path)
    meta_path = attach_metadata(manual, METADATA_VERSION)

    print("✅ Organizare completă")
    print("Manual:", manual)
    print("Symlink:", link)
    print("Metadata:", meta_path)

    return {
        "status": "ok",
        "manual": manual,
        "symlink": link,
        "metadata": meta_path
    }


# --- RUN DEMO LOCAL / FASTAPI ---
if __name__ == "__main__":
    import uvicorn
    BASE_DIR = Path(__file__).resolve().parent
    library_path = BASE_DIR / "data" / "library"
    clawbot_path = BASE_DIR / "data" / "clawbot_view"
    organize(str(library_path), str(clawbot_path))
    # Pornire FastAPI pentru upload
    uvicorn.run(app, host="127.0.0.1", port=8000)


