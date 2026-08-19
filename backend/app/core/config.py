from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg2://bip:bip@db:5432/bip"
    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_minutes: int = 60 * 24 * 7
    cors_origins: list[str] = ["http://localhost:5173"]
    quote_refresh_interval_minutes: int = 15
    initial_credit_amount: str = "100000.00"
    fee_rate_bps: int = 10  # 0.10%
    testing: bool = False


settings = Settings()
