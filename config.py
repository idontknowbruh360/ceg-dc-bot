import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

load_dotenv(ENV_PATH)

class Settings:
    DISCORD_TOKEN: str = os.getenv("DISCORD_TOKEN", "")
    DEFAULT_GUILD_ID: str = os.getenv("DEFAULT_GUILD_ID", "")
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    SECRET_KEY: str = os.getenv("SECRET_KEY", "cegbot_secret_key")
    DB_PATH: Path = BASE_DIR / "data.db"

    @classmethod
    def save_env_setting(cls, key: str, value: str):
        setattr(cls, key, value)
        env_dict = {}
        if ENV_PATH.exists():
            with open(ENV_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        env_dict[k.strip()] = v.strip()
        
        env_dict[key] = value
        
        with open(ENV_PATH, "w", encoding="utf-8") as f:
            for k, v in env_dict.items():
                f.write(f"{k}={v}\n")

settings = Settings()
