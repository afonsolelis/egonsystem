import logging
from typing import List, Tuple, Callable, Optional
from datetime import datetime

from .github_client import GitHubClient, CircuitBreakerError
from .datalake import DataLake
from .models import Repository, Commit, PullRequest
from .config import Config

logger = logging.getLogger(__name__)

class DataCollector:
    def __init__(self):
        Config.validate()
        self.github_client = None
        self.datalake = DataLake()
        
    def _ensure_github_client(self):
        """Initialize GitHub client only when needed"""
        if self.github_client is None:
            Config.validate_github_token()
            self.github_client = GitHubClient(Config.GITHUB_TOKEN)
    
    def collect_all_data(self, progress_callback: Optional[Callable[[int, int, str], None]] = None) -> str:
        logger.info("Starting data collection for all repositories")
        self._ensure_github_client()
        
        repositories = []
        all_commits = []
        all_pull_requests = []
        
        repo_names = Config.get_all_repositories()
        
        if not repo_names:
            logger.warning("No repositories configured")
            return None
        
        total_repos = len(repo_names)
        
        for i, repo_name in enumerate(repo_names, 1):
            try:
                if progress_callback:
                    progress_callback(i-1, total_repos, f"Processando: {repo_name}")
                
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
                
                # Collect pull requests (passando commits coletados para otimizar)
                pull_requests = self.github_client.get_pull_requests_from_repo(repo_name, commits)
                all_pull_requests.extend(pull_requests)
                logger.info(f"Collected {len(pull_requests)} pull requests from {repo_name}")
                
                if progress_callback:
                    progress_callback(i, total_repos, f"✅ {repo_name} - {len(commits)} commits, {len(pull_requests)} PRs")
                
            except CircuitBreakerError as e:
                # Parar completamente a coleta - não salvar dados parciais
                error_msg = f"🔴 Coleta interrompida: {str(e)}"
                logger.error(error_msg)
                if progress_callback:
                    progress_callback(i, total_repos, error_msg)
                raise e  # Propagar o erro para o front
            except Exception as e:
                logger.error(f"Error processing repository {repo_name}: {e}")
                if progress_callback:
                    progress_callback(i, total_repos, f"❌ Erro em {repo_name}: {str(e)}")
                continue
        
        # Create snapshot
        if progress_callback:
            progress_callback(total_repos, total_repos, "Criando snapshot no Supabase...")
            
        snapshot_id = self.datalake.create_snapshot(repositories, all_commits, all_pull_requests)
        
        logger.info(f"Data collection completed. Created snapshot: {snapshot_id}")
        logger.info(f"Total: {len(repositories)} repos, {len(all_commits)} commits, {len(all_pull_requests)} PRs")
        
        return snapshot_id
    
    def stop_collection(self):
        """Para a coleta de dados em andamento"""
        if self.github_client:
            self.github_client.stop_execution()
        logger.info("Collection stop requested")
    
    def get_snapshots_summary(self) -> List[dict]:
        return self.datalake.list_snapshots()
    
    def load_snapshot(self, snapshot_id: str = None):
        if not snapshot_id:
            snapshot_id = self.datalake.get_latest_snapshot()
        
        if not snapshot_id:
            logger.warning("No snapshots available")
            return None
        
        return self.datalake.load_snapshot_data(snapshot_id)
    
