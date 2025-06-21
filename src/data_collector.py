import logging
from typing import List, Tuple
from datetime import datetime

from .github_client import GitHubClient
from .datalake import DataLake
from .models import Repository, Commit, PullRequest
from .config import Config

logger = logging.getLogger(__name__)

class DataCollector:
    def __init__(self):
        Config.validate()
        self.github_client = GitHubClient(Config.GITHUB_TOKEN)
        self.datalake = DataLake()
    
    def collect_all_data(self) -> str:
        logger.info("Starting data collection for all repositories")
        
        repositories = []
        all_commits = []
        all_pull_requests = []
        
        repo_names = Config.get_all_repositories()
        
        if not repo_names:
            logger.warning("No repositories configured")
            return None
        
        for repo_name in repo_names:
            try:
                logger.info(f"Processing repository: {repo_name}")
                
                # Create repository record
                repository = Repository(
                    repo_name=repo_name,
                    last_updated=datetime.now().isoformat()
                )
                repositories.append(repository)
                
                # Collect commits
                commits = self.github_client.get_commits_from_repo(repo_name)
                all_commits.extend(commits)
                logger.info(f"Collected {len(commits)} commits from {repo_name}")
                
                # Collect pull requests
                pull_requests = self.github_client.get_pull_requests_from_repo(repo_name)
                all_pull_requests.extend(pull_requests)
                logger.info(f"Collected {len(pull_requests)} pull requests from {repo_name}")
                
            except Exception as e:
                logger.error(f"Error processing repository {repo_name}: {e}")
                continue
        
        # Create snapshot
        snapshot_id = self.datalake.create_snapshot(repositories, all_commits, all_pull_requests)
        
        logger.info(f"Data collection completed. Created snapshot: {snapshot_id}")
        logger.info(f"Total: {len(repositories)} repos, {len(all_commits)} commits, {len(all_pull_requests)} PRs")
        
        return snapshot_id
    
    def get_snapshots_summary(self) -> List[dict]:
        return self.datalake.list_snapshots()
    
    def load_snapshot(self, snapshot_id: str = None):
        if not snapshot_id:
            snapshot_id = self.datalake.get_latest_snapshot()
        
        if not snapshot_id:
            logger.warning("No snapshots available")
            return None
        
        return self.datalake.load_snapshot_data(snapshot_id)