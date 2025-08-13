import os
from typing import List
from dotenv import load_dotenv

load_dotenv(override=True)

class Config:
    GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
    INTERNAL_REPOSITORIES = os.getenv('INTERNAL_REPOSITORIES', '').split(',') if os.getenv('INTERNAL_REPOSITORIES') else []
    PUBLIC_REPOSITORIES = os.getenv('PUBLIC_REPOSITORIES', '').split(',') if os.getenv('PUBLIC_REPOSITORIES') else []
    DATALAKE_PATH = os.getenv('DATALAKE_PATH', './datalake')
    SNAPSHOTS_PATH = os.getenv('SNAPSHOTS_PATH', './datalake/snapshots')
    APP_NAME = os.getenv('APP_NAME', 'FourSystem')
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

    SUPABASE_URL = os.getenv('NEXT_PUBLIC_SUPABASE_URL')
    SUPABASE_ANON_KEY = os.getenv('NEXT_PUBLIC_SUPABASE_ANON_KEY')
    SUPABASE_BUCKET = os.getenv('SUPABASE_BUCKET', 'snapshots')

    @classmethod
    def get_all_repositories(cls) -> List[str]:
        return [repo.strip() for repo in cls.INTERNAL_REPOSITORIES + cls.PUBLIC_REPOSITORIES if repo.strip()]

    @classmethod
    def validate(cls) -> bool:
        # In deployment environments, GITHUB_TOKEN might not be available
        # Only validate when actually needed for data collection
        if not cls.SUPABASE_URL or not cls.SUPABASE_ANON_KEY:
            raise ValueError("Supabase configuration (URL and ANON_KEY) is required")
        return True
    
    @classmethod
    def validate_github_token(cls) -> bool:
        if not cls.GITHUB_TOKEN:
            raise ValueError("GITHUB_TOKEN is required for data collection")
        return True
