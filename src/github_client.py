from typing import List, Generator, Optional, Callable
from github import Github, GithubException, RateLimitExceededException
from github.Repository import Repository
from github.Commit import Commit as GHCommit
from github.PullRequest import PullRequest as GHPullRequest
import logging
import time
import threading
from datetime import datetime, timedelta

from .models import Commit, PullRequest
from .config import Config

logger = logging.getLogger(__name__)

class GitHubClient:
    def __init__(self, token: str):
        self.client = Github(token)
        self.user = self.client.get_user()
        self.should_stop = threading.Event()
        self.rate_limit_reset_time = None
        
    def set_stop_callback(self, callback: Callable[[], bool]):
        """Define callback para verificar se deve parar a execução"""
        self.should_stop_callback = callback
        
    def check_should_stop(self) -> bool:
        """Verifica se deve parar a execução"""
        return self.should_stop.is_set() or (hasattr(self, 'should_stop_callback') and self.should_stop_callback())
    
    def stop_execution(self):
        """Para a execução atual"""
        self.should_stop.set()
        
    def get_rate_limit_info(self) -> dict:
        """Obtém informações sobre rate limit"""
        try:
            rate_limit = self.client.get_rate_limit()
            return {
                'remaining': rate_limit.core.remaining,
                'limit': rate_limit.core.limit,
                'reset_time': rate_limit.core.reset,
                'used': rate_limit.core.limit - rate_limit.core.remaining
            }
        except Exception as e:
            logger.warning(f"Could not get rate limit info: {e}")
            return {'remaining': 0, 'limit': 5000, 'reset_time': None, 'used': 5000}
    
    def wait_for_rate_limit(self, progress_callback: Optional[Callable[[str], None]] = None) -> bool:
        """Aguarda o reset do rate limit."""
        rate_info = self.get_rate_limit_info()
        
        if rate_info['remaining'] > 10:  # Buffer de segurança
            return True
            
        if not rate_info['reset_time']:
            logger.warning("No rate limit reset time available")
            return False
            
        wait_seconds = (rate_info['reset_time'] - datetime.now()).total_seconds()
        
        if wait_seconds <= 0:
            return True
            
        logger.warning(f"Rate limit exceeded. Waiting {wait_seconds:.0f} seconds...")
        time.sleep(min(wait_seconds, 3600))  # Max 1 hora
        return True
    
    def get_repository(self, repo_name: str) -> Optional[Repository]:
        """Obtém repositório com rate limiting inteligente"""
        if self.check_should_stop():
            return None
            
        try:
            # Verifica rate limit antes da requisição
            if not self.wait_for_rate_limit():
                return None
                
            return self.client.get_repo(repo_name)
        except RateLimitExceededException:
            logger.warning(f"Rate limit exceeded while accessing {repo_name}")
            if not self.wait_for_rate_limit():
                return None
            try:
                return self.client.get_repo(repo_name)
            except Exception as e:
                logger.error(f"Failed to access repository {repo_name} after rate limit wait: {e}")
                return None
        except GithubException as e:
            logger.error(f"Error accessing repository {repo_name}: {e}")
            return None
    
    def get_commits_from_repo(self, repo_name: str) -> List[Commit]:
        commits = []
        
        if self.check_should_stop():
            return commits
            
        try:
            repo = self.get_repository(repo_name)
            if not repo:
                return commits
                
            commit_count = 0
            for gh_commit in repo.get_commits():
                if self.check_should_stop():
                    logger.info(f"Stopped collecting commits from {repo_name} at user request")
                    break
                    
                # Verifica rate limit a cada 50 commits
                if commit_count % 50 == 0 and commit_count > 0:
                    if not self.wait_for_rate_limit():
                        break
                
                try:
                    author = gh_commit.commit.author or {}
                    commit = Commit(
                        sha=gh_commit.sha,
                        message=gh_commit.commit.message,
                        author=getattr(author, 'name', '') or '',
                        email=getattr(author, 'email', '') or '',
                        date=getattr(author, 'date', None).isoformat() if getattr(author, 'date', None) else None,
                        url=gh_commit.html_url,
                        repo_name=repo_name
                    )
                    commits.append(commit)
                    commit_count += 1
                    
                except Exception as e:
                    logger.warning(f"Error processing commit {gh_commit.sha} from {repo_name}: {e}")
                    continue
                
        except RateLimitExceededException:
            logger.warning(f"Rate limit exceeded while fetching commits from {repo_name}")
            if self.wait_for_rate_limit():
                # Retry uma vez após rate limit
                return self.get_commits_from_repo(repo_name)
        except GithubException as e:
            if 'Git Repository is empty' in str(e):
                logger.warning(f"Repository {repo_name} is empty")
            else:
                logger.error(f"Error fetching commits from {repo_name}: {e}")
                
        return commits
    
    def get_pull_requests_from_repo(self, repo_name: str) -> List[PullRequest]:
        pull_requests = []
        
        if self.check_should_stop():
            return pull_requests
            
        try:
            repo = self.get_repository(repo_name)
            if not repo:
                return pull_requests
                
            pr_count = 0
            for gh_pr in repo.get_pulls(state='all', sort='created', direction='desc'):
                if self.check_should_stop():
                    logger.info(f"Stopped collecting PRs from {repo_name} at user request")
                    break
                    
                # Verifica rate limit a cada 20 PRs
                if pr_count % 20 == 0 and pr_count > 0:
                    if not self.wait_for_rate_limit():
                        break
                
                try:
                    pr = PullRequest(
                        number=str(gh_pr.number),
                        title=gh_pr.title,
                        author=gh_pr.user.login,
                        email=gh_pr.user.email or '',
                        created_at=gh_pr.created_at.isoformat() if gh_pr.created_at else None,
                        state=gh_pr.state,
                        comments=str(gh_pr.comments),
                        review_comments=str(gh_pr.review_comments),
                        commits=str([c.sha for c in gh_pr.get_commits()]),
                        url=gh_pr.html_url,
                        repo_name=repo_name
                    )
                    pull_requests.append(pr)
                    pr_count += 1
                    
                except Exception as e:
                    logger.warning(f"Error processing PR #{gh_pr.number} from {repo_name}: {e}")
                    continue
                
        except RateLimitExceededException:
            logger.warning(f"Rate limit exceeded while fetching PRs from {repo_name}")
            if self.wait_for_rate_limit():
                # Retry uma vez após rate limit
                return self.get_pull_requests_from_repo(repo_name)
        except GithubException as e:
            if 'Git Repository is empty' in str(e):
                logger.warning(f"Repository {repo_name} is empty")
            else:
                logger.error(f"Error fetching pull requests from {repo_name}: {e}")
                
        return pull_requests