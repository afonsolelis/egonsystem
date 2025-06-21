from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, List, Dict, Any
import json

@dataclass
class Commit:
    sha: str
    message: str
    author: str
    email: str
    date: Optional[str]
    url: str
    repo_name: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class PullRequest:
    number: str
    title: str
    author: str
    email: str
    created_at: Optional[str]
    state: str
    comments: str
    review_comments: str
    commits: str
    url: str
    repo_name: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class Repository:
    repo_name: str
    last_updated: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class SnapshotMetadata:
    timestamp: str
    repositories_count: int
    commits_count: int
    pull_requests_count: int
    snapshot_id: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)