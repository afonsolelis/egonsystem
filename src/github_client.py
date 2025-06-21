from typing import List, Generator
from github import Github, GithubException
from github.Repository import Repository
from github.Commit import Commit as GHCommit
from github.PullRequest import PullRequest as GHPullRequest
import logging

from .models import Commit, PullRequest
from .config import Config

logger = logging.getLogger(__name__)

class GitHubClient:
    def __init__(self, token: str):
        self.client = Github(token)
        self.user = self.client.get_user()
    
    def get_repository(self, repo_name: str) -> Repository:
        try:
            return self.client.get_repo(repo_name)
        except GithubException as e:
            logger.error(f"Error accessing repository {repo_name}: {e}")
            raise
    
    def get_commits_from_repo(self, repo_name: str) -> List[Commit]:
        commits = []
        try:
            repo = self.get_repository(repo_name)
            for gh_commit in repo.get_commits():
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
                
        except GithubException as e:
            if 'Git Repository is empty' in str(e):
                logger.warning(f"Repository {repo_name} is empty")
            else:
                logger.error(f"Error fetching commits from {repo_name}: {e}")
                
        return commits
    
    def get_pull_requests_from_repo(self, repo_name: str) -> List[PullRequest]:
        pull_requests = []
        try:
            repo = self.get_repository(repo_name)
            for gh_pr in repo.get_pulls(state='all', sort='created', direction='desc'):
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
                
        except GithubException as e:
            if 'Git Repository is empty' in str(e):
                logger.warning(f"Repository {repo_name} is empty")
            else:
                logger.error(f"Error fetching pull requests from {repo_name}: {e}")
                
        return pull_requests