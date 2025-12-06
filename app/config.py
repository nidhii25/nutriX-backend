import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings loaded from environment variables.

    Currently only exposes DATABASE_URL, which is read once at startup.
    """

    def __init__(self) -> None:
        # May be None if not configured; the database layer will fail fast
        # when attempting to use an empty URL.
        self.DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")


settings = Settings()
