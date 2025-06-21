import os
import json
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

from .models import Commit, PullRequest, Repository, SnapshotMetadata
from .config import Config

logger = logging.getLogger(__name__)

class DataLake:
    def __init__(self, base_path: str = None):
        self.base_path = Path(base_path or Config.DATALAKE_PATH)
        self.snapshots_path = Path(Config.SNAPSHOTS_PATH)
        self._ensure_directories()
    
    def _ensure_directories(self):
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.snapshots_path.mkdir(parents=True, exist_ok=True)
    
    def create_snapshot(self, repositories: List[Repository], 
                       commits: List[Commit], 
                       pull_requests: List[PullRequest]) -> str:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        snapshot_id = f"snapshot_{timestamp}"
        snapshot_dir = self.snapshots_path / snapshot_id
        snapshot_dir.mkdir(exist_ok=True)
        
        try:
            # Convert to DataFrames and save as Parquet
            if repositories:
                repos_df = pd.DataFrame([repo.to_dict() for repo in repositories])
                repos_df.to_parquet(snapshot_dir / "repositories.parquet", index=False)
            
            if commits:
                commits_df = pd.DataFrame([commit.to_dict() for commit in commits])
                commits_df.to_parquet(snapshot_dir / "commits.parquet", index=False)
            
            if pull_requests:
                prs_df = pd.DataFrame([pr.to_dict() for pr in pull_requests])
                prs_df.to_parquet(snapshot_dir / "pull_requests.parquet", index=False)
            
            # Create metadata
            metadata = SnapshotMetadata(
                timestamp=timestamp,
                repositories_count=len(repositories),
                commits_count=len(commits),
                pull_requests_count=len(pull_requests),
                snapshot_id=snapshot_id
            )
            
            with open(snapshot_dir / "metadata.json", "w") as f:
                json.dump(metadata.to_dict(), f, indent=2)
            
            logger.info(f"Snapshot created: {snapshot_id}")
            return snapshot_id
            
        except Exception as e:
            logger.error(f"Error creating snapshot: {e}")
            raise
    
    def list_snapshots(self) -> List[Dict[str, Any]]:
        snapshots = []
        for snapshot_dir in self.snapshots_path.iterdir():
            if snapshot_dir.is_dir():
                metadata_file = snapshot_dir / "metadata.json"
                if metadata_file.exists():
                    try:
                        with open(metadata_file, "r") as f:
                            metadata = json.load(f)
                        snapshots.append(metadata)
                    except Exception as e:
                        logger.warning(f"Error reading metadata for {snapshot_dir.name}: {e}")
        
        return sorted(snapshots, key=lambda x: x['timestamp'], reverse=True)
    
    def load_snapshot_data(self, snapshot_id: str) -> Dict[str, pd.DataFrame]:
        snapshot_dir = self.snapshots_path / snapshot_id
        data = {}
        
        try:
            if (snapshot_dir / "repositories.parquet").exists():
                data['repositories'] = pd.read_parquet(snapshot_dir / "repositories.parquet")
            
            if (snapshot_dir / "commits.parquet").exists():
                data['commits'] = pd.read_parquet(snapshot_dir / "commits.parquet")
            
            if (snapshot_dir / "pull_requests.parquet").exists():
                data['pull_requests'] = pd.read_parquet(snapshot_dir / "pull_requests.parquet")
                
        except Exception as e:
            logger.error(f"Error loading snapshot {snapshot_id}: {e}")
            raise
        
        return data
    
    def get_latest_snapshot(self) -> Optional[str]:
        snapshots = self.list_snapshots()
        return snapshots[0]['snapshot_id'] if snapshots else None
    
    def delete_snapshot(self, snapshot_id: str) -> bool:
        snapshot_dir = self.snapshots_path / snapshot_id
        try:
            if snapshot_dir.exists():
                import shutil
                shutil.rmtree(snapshot_dir)
                logger.info(f"Snapshot {snapshot_id} deleted")
                return True
        except Exception as e:
            logger.error(f"Error deleting snapshot {snapshot_id}: {e}")
        return False