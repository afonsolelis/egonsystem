import os
from typing import List
from dotenv import load_dotenv

load_dotenv()

class Config:
    GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
    INTERNAL_REPOSITORIES = os.getenv('INTERNAL_REPOSITORIES', '').split(',') if os.getenv('INTERNAL_REPOSITORIES') else []
    PUBLIC_REPOSITORIES = os.getenv('PUBLIC_REPOSITORIES', '').split(',') if os.getenv('PUBLIC_REPOSITORIES') else []
    DATALAKE_PATH = os.getenv('DATALAKE_PATH', './datalake')
    SNAPSHOTS_PATH = os.getenv('SNAPSHOTS_PATH', './datalake/snapshots')
    APP_NAME = os.getenv('APP_NAME', 'EgonSystem')
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    @classmethod
    def get_all_repositories(cls) -> List[str]:
        return [repo.strip() for repo in cls.INTERNAL_REPOSITORIES + cls.PUBLIC_REPOSITORIES if repo.strip()]
    
    @classmethod
    def validate(cls) -> bool:
        if not cls.GITHUB_TOKEN:
            raise ValueError("GITHUB_TOKEN is required")
        return True