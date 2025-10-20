import os
import json
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
import io
from supabase import create_client, Client

from .models import Commit, PullRequest, Repository, SnapshotMetadata
from .config import Config

logger = logging.getLogger(__name__)

class DataLake:
    def __init__(self, base_path: str = None):
        self.base_path = Path(base_path or Config.DATALAKE_PATH)
        self.snapshots_path = Path(Config.SNAPSHOTS_PATH)
        self.storage_backend = Config.STORAGE_BACKEND
        self._ensure_directories()

        self.supabase: Optional[Client] = None
        self.bucket_name = None
        if self.storage_backend == 'supabase':
            self.supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_ANON_KEY)
            self.bucket_name = Config.SUPABASE_BUCKET
            self._ensure_bucket()

    def _ensure_bucket(self):
        try:
            buckets = self.supabase.storage.list_buckets()
            bucket_names = [bucket.name for bucket in buckets]
            if self.bucket_name not in bucket_names:
                # Create bucket with public access
                self.supabase.storage.create_bucket(
                    self.bucket_name,
                    options={"public": True}
                )
                logger.info(f"Created bucket: {self.bucket_name}")
        except Exception as e:
            logger.warning(f"Could not create bucket {self.bucket_name}: {e}")

    def _ensure_directories(self):
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.snapshots_path.mkdir(parents=True, exist_ok=True)

    def create_snapshot(self, repositories: List[Repository],
                       commits: List[Commit],
                       pull_requests: List[PullRequest]) -> str:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        snapshot_id = f"snapshot_{timestamp}"

        try:
            if self.storage_backend == 'supabase':
                # Convert to DataFrames and upload as Parquet to Supabase
                if repositories:
                    repos_df = pd.DataFrame([repo.to_dict() for repo in repositories])
                    buffer = io.BytesIO()
                    repos_df.to_parquet(buffer, index=False)
                    buffer.seek(0)

                    file_path = f"{snapshot_id}/repositories.parquet"
                    self.supabase.storage.from_(self.bucket_name).upload(
                        file_path, buffer.getvalue(),
                        file_options={"upsert": "true"}
                    )

                if commits:
                    commits_df = pd.DataFrame([commit.to_dict() for commit in commits])
                    buffer = io.BytesIO()
                    commits_df.to_parquet(buffer, index=False)
                    buffer.seek(0)

                    file_path = f"{snapshot_id}/commits.parquet"
                    self.supabase.storage.from_(self.bucket_name).upload(
                        file_path, buffer.getvalue(),
                        file_options={"upsert": "true"}
                    )

                if pull_requests:
                    prs_df = pd.DataFrame([pr.to_dict() for pr in pull_requests])
                    buffer = io.BytesIO()
                    prs_df.to_parquet(buffer, index=False)
                    buffer.seek(0)

                    file_path = f"{snapshot_id}/pull_requests.parquet"
                    self.supabase.storage.from_(self.bucket_name).upload(
                        file_path, buffer.getvalue(),
                        file_options={"upsert": "true"}
                    )
            else:
                # Local filesystem backend
                snapshot_dir = self.snapshots_path / snapshot_id
                snapshot_dir.mkdir(parents=True, exist_ok=True)

                if repositories:
                    repos_df = pd.DataFrame([repo.to_dict() for repo in repositories])
                    repos_df.to_parquet(snapshot_dir / 'repositories.parquet', index=False)

                if commits:
                    commits_df = pd.DataFrame([commit.to_dict() for commit in commits])
                    commits_df.to_parquet(snapshot_dir / 'commits.parquet', index=False)

                if pull_requests:
                    prs_df = pd.DataFrame([pr.to_dict() for pr in pull_requests])
                    prs_df.to_parquet(snapshot_dir / 'pull_requests.parquet', index=False)

            # Create metadata
            metadata = SnapshotMetadata(
                timestamp=timestamp,
                repositories_count=len(repositories),
                commits_count=len(commits),
                pull_requests_count=len(pull_requests),
                snapshot_id=snapshot_id
            )

            # Save metadata
            metadata_json = json.dumps(metadata.to_dict(), indent=2)
            if self.storage_backend == 'supabase':
                file_path = f"{snapshot_id}/metadata.json"
                self.supabase.storage.from_(self.bucket_name).upload(
                    file_path, metadata_json.encode('utf-8'),
                    file_options={"upsert": "true"}
                )
            else:
                snapshot_dir = self.snapshots_path / snapshot_id
                with open(snapshot_dir / 'metadata.json', 'w', encoding='utf-8') as f:
                    f.write(metadata_json)

            logger.info(f"Snapshot created: {snapshot_id}")
            return snapshot_id

        except Exception as e:
            logger.error(f"Error creating snapshot: {e}")
            raise

    def list_snapshots(self) -> List[Dict[str, Any]]:
        snapshots = []
        try:
            if self.storage_backend == 'supabase':
                items = self.supabase.storage.from_(self.bucket_name).list()
                for item in items:
                    snapshot_id = item['name']
                    try:
                        metadata_path = f"{snapshot_id}/metadata.json"
                        response = self.supabase.storage.from_(self.bucket_name).download(metadata_path)
                        metadata = json.loads(response.decode('utf-8'))
                        snapshots.append(metadata)
                        logger.info(f"Loaded metadata for snapshot: {snapshot_id}")
                    except Exception as e:
                        logger.warning(f"Error reading metadata for {snapshot_id}: {e}")
            else:
                # Local listing
                if self.snapshots_path.exists():
                    for entry in self.snapshots_path.iterdir():
                        if entry.is_dir():
                            metadata_file = entry / 'metadata.json'
                            if metadata_file.exists():
                                try:
                                    with open(metadata_file, 'r', encoding='utf-8') as f:
                                        metadata = json.load(f)
                                        snapshots.append(metadata)
                                except Exception as e:
                                    logger.warning(f"Error reading metadata for {entry.name}: {e}")
        except Exception as e:
            logger.error(f"Error listing snapshots: {e}")
        return sorted(snapshots, key=lambda x: x['timestamp'], reverse=True)

    def load_snapshot_data(self, snapshot_id: str) -> Dict[str, pd.DataFrame]:
        data = {}
        try:
            if self.storage_backend == 'supabase':
                try:
                    repos_path = f"{snapshot_id}/repositories.parquet"
                    repos_data = self.supabase.storage.from_(self.bucket_name).download(repos_path)
                    data['repositories'] = pd.read_parquet(io.BytesIO(repos_data))
                except:
                    pass
                try:
                    commits_path = f"{snapshot_id}/commits.parquet"
                    commits_data = self.supabase.storage.from_(self.bucket_name).download(commits_path)
                    data['commits'] = pd.read_parquet(io.BytesIO(commits_data))
                except:
                    pass
                try:
                    prs_path = f"{snapshot_id}/pull_requests.parquet"
                    prs_data = self.supabase.storage.from_(self.bucket_name).download(prs_path)
                    data['pull_requests'] = pd.read_parquet(io.BytesIO(prs_data))
                except:
                    pass
            else:
                snapshot_dir = self.snapshots_path / snapshot_id
                try:
                    repos_file = snapshot_dir / 'repositories.parquet'
                    if repos_file.exists():
                        data['repositories'] = pd.read_parquet(repos_file)
                except:
                    pass
                try:
                    commits_file = snapshot_dir / 'commits.parquet'
                    if commits_file.exists():
                        data['commits'] = pd.read_parquet(commits_file)
                except:
                    pass
                try:
                    prs_file = snapshot_dir / 'pull_requests.parquet'
                    if prs_file.exists():
                        data['pull_requests'] = pd.read_parquet(prs_file)
                except:
                    pass
        except Exception as e:
            logger.error(f"Error loading snapshot {snapshot_id}: {e}")
            raise
        return data

    def get_latest_snapshot(self) -> Optional[str]:
        snapshots = self.list_snapshots()
        return snapshots[0]['snapshot_id'] if snapshots else None

    def delete_snapshot(self, snapshot_id: str) -> bool:
        try:
            if self.storage_backend == 'supabase':
                files = self.supabase.storage.from_(self.bucket_name).list(snapshot_id)
                for file in files:
                    file_path = f"{snapshot_id}/{file['name']}"
                    self.supabase.storage.from_(self.bucket_name).remove([file_path])
            else:
                snapshot_dir = self.snapshots_path / snapshot_id
                if snapshot_dir.exists() and snapshot_dir.is_dir():
                    for path in snapshot_dir.glob('**/*'):
                        if path.is_file():
                            path.unlink()
                    for path in sorted(snapshot_dir.glob('**/*'), reverse=True):
                        if path.is_dir():
                            path.rmdir()
                    snapshot_dir.rmdir()
            logger.info(f"Snapshot {snapshot_id} deleted")
            return True
        except Exception as e:
            logger.error(f"Error deleting snapshot {snapshot_id}: {e}")
            return False
