import logging
import sys

from src.data_collector import DataCollector
from src.config import Config


def main() -> int:
    logging.basicConfig(level=getattr(logging, Config.LOG_LEVEL, "INFO"))
    logger = logging.getLogger("update_snapshot")

    try:
        logger.info("Iniciando coleta de dados para geração de snapshot...")
        collector = DataCollector()
        snapshot_id = collector.collect_all_data()
        if snapshot_id:
            logger.info(f"Snapshot criado com sucesso: {snapshot_id}")
            print(snapshot_id)
            return 0
        else:
            logger.error("Falha ao criar snapshot (retorno vazio).")
            return 2
    except Exception as e:
        logger.exception(f"Erro durante a geração do snapshot: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

