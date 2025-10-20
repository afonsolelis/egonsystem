import logging
import sys
from dotenv import load_dotenv

# Ensure project modules are importable when invoked directly
try:
    from src.data_collector import DataCollector
except Exception as e:
    print(f"Failed to import project modules: {e}", file=sys.stderr)
    sys.exit(1)


def main() -> int:
    load_dotenv(override=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    logger = logging.getLogger("collect_snapshot")

    try:
        collector = DataCollector()
        snapshot_id = collector.collect_all_data()
        if snapshot_id:
            logger.info(f"Snapshot created successfully: {snapshot_id}")
            return 0
        logger.warning("No snapshot created (no repositories configured or errors during collection)")
        return 2
    except Exception as e:
        logger.exception(f"Snapshot collection failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())


