import os
import json
from pathlib import Path
import logging
from typing import List

from dotenv import load_dotenv
from supabase import create_client, Client


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("migrate")


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def main() -> None:
    load_dotenv(override=True)

    url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    key = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
    bucket = os.getenv("SUPABASE_BUCKET", "snapshots")

    if not url or not key:
        raise SystemExit("Supabase credentials missing. Set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY in .env")

    supabase: Client = create_client(url, key)

    local_base = Path(os.getenv("SNAPSHOTS_PATH", "./data/snapshots"))
    ensure_dir(local_base)

    logger.info(f"Listing snapshots in Supabase bucket '{bucket}'...")
    try:
        items: List[dict] = supabase.storage.from_(bucket).list()
    except Exception as e:
        raise SystemExit(f"Failed to list bucket '{bucket}': {e}")

    if not items:
        logger.info("No snapshots found in bucket.")
        return

    total = len(items)
    for idx, item in enumerate(items, 1):
        snapshot_id = item.get("name") or item.get("id")
        if not snapshot_id:
            logger.warning(f"Skipping item without name/id: {item}")
            continue

        logger.info(f"[{idx}/{total}] Migrating {snapshot_id}...")
        snapshot_dir = local_base / snapshot_id
        ensure_dir(snapshot_dir)

        for filename in ["repositories.parquet", "commits.parquet", "pull_requests.parquet", "metadata.json"]:
            remote_path = f"{snapshot_id}/{filename}"
            local_path = snapshot_dir / filename
            try:
                blob = supabase.storage.from_(bucket).download(remote_path)
                if isinstance(blob, bytes):
                    data = blob
                else:
                    # Some clients may return str
                    data = blob.encode("utf-8")
                with open(local_path, "wb") as f:
                    f.write(data)
                logger.info(f"  - Downloaded {filename}")
            except Exception as e:
                logger.warning(f"  - Skipped {filename}: {e}")

    logger.info("Migration completed. Local snapshots available in 'data/snapshots/'.")


if __name__ == "__main__":
    main()


