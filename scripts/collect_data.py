#!/usr/bin/env python3

import sys
import os
import logging
from pathlib import Path

# Add the parent directory to Python path to import src modules
sys.path.append(str(Path(__file__).parent.parent))

from src.data_collector import DataCollector
from src.config import Config

def setup_logging():
    logging.basicConfig(
        level=getattr(logging, Config.LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def main():
    """Collect data from all configured repositories and create a snapshot."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Starting data collection...")
        
        # Validate configuration
        Config.validate()
        
        # Initialize data collector
        collector = DataCollector()
        
        # Collect all data and create snapshot
        snapshot_id = collector.collect_all_data()
        
        if snapshot_id:
            logger.info(f"✅ Data collection completed successfully!")
            logger.info(f"📸 Snapshot created: {snapshot_id}")
            
            # Show summary
            snapshots = collector.get_snapshots_summary()
            latest = snapshots[0] if snapshots else None
            if latest:
                logger.info(f"📊 Summary:")
                logger.info(f"   - Repositories: {latest['repositories_count']}")
                logger.info(f"   - Commits: {latest['commits_count']}")
                logger.info(f"   - Pull Requests: {latest['pull_requests_count']}")
        else:
            logger.error("❌ Data collection failed")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"❌ Error during data collection: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()