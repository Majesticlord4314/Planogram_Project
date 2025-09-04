import argparse
import shutil
from pathlib import Path


def merge_folders(src_dirs, dest_dir: Path):
    dest_dir.mkdir(parents=True, exist_ok=True)
    copied = 0
    skipped = 0
    collisions = 0

    for src in src_dirs:
        src_path = Path(src)
        if not src_path.exists():
            print(f"[WARN] Source not found: {src_path}")
            continue
        for p in sorted(src_path.glob("*.jpg")):
            target = dest_dir / p.name
            if target.exists():
                # add numeric suffix to avoid overwrite
                stem, ext = target.stem, target.suffix
                i = 2
                while (dest_dir / f"{stem}-{i}{ext}").exists():
                    i += 1
                target = dest_dir / f"{stem}-{i}{ext}"
                collisions += 1
            try:
                shutil.copy2(p, target)
                copied += 1
            except Exception as e:
                print(f"[ERROR] Failed to copy {p} -> {target}: {e}")
                skipped += 1
    return {"copied": copied, "skipped": skipped, "collisions": collisions}


def main():
    parser = argparse.ArgumentParser(description="Merge two image folders into a combined folder")
    parser.add_argument("src", nargs="+", help="Source folders with images (e.g., .../2025-08-22 17-44-17 .../2025-08-22 17-46-29)")
    parser.add_argument("--dest", default="pdf_databank/output/images/combined", help="Destination folder for merged images")
    args = parser.parse_args()

    summary = merge_folders(args.src, Path(args.dest))
    print("Merge summary:", summary)
    print("Destination:", args.dest)


if __name__ == "__main__":
    main()

