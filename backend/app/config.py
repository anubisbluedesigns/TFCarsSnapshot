import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    db_backend: str = os.getenv("DB_BACKEND", "sqlite")  # "sqlite" or "snowflake"
    sqlite_path: str = os.getenv("SQLITE_PATH", "dealership_inventory.db")

    # Dedicated, least-privilege identity for this app only — isolated from the
    # payroll (ANUBISBLUEDESIGNS) and call-logger (call_logger_app) users so
    # nothing here can affect either of those. See sql/provision_snowflake.sql.
    snowflake_account: str = os.getenv("SNOWFLAKE_ACCOUNT", "TXFRMSX-HV94520")
    snowflake_user: str = os.getenv("SNOWFLAKE_USER", "INVENTORY_APP")
    snowflake_private_key_path: str = os.getenv("SNOWFLAKE_PRIVATE_KEY_PATH", "inventory_rsa_key.pem")
    # Alternative to the path above — base64 of the whole .pem file contents.
    # Set this instead of SNOWFLAKE_PRIVATE_KEY_PATH when there's no writable
    # filesystem to drop a key file on (e.g. Render).
    snowflake_private_key_b64: str = os.getenv("SNOWFLAKE_PRIVATE_KEY_B64", "")
    snowflake_warehouse: str = os.getenv("SNOWFLAKE_WAREHOUSE", "INVENTORY_WH")
    snowflake_database: str = os.getenv("SNOWFLAKE_DATABASE", "TFC_INVENTORY")
    snowflake_schema: str = os.getenv("SNOWFLAKE_SCHEMA", "INVENTORY")
    snowflake_role: str = os.getenv("SNOWFLAKE_ROLE", "INVENTORY_APP_ROLE")
    snowflake_insecure_mode: bool = os.getenv("SNOWFLAKE_INSECURE_MODE", "false").lower() == "true"

    google_client_id: str = os.getenv("GOOGLE_CLIENT_ID", "")
    # Explicit opt-in for the /auth/dev-login shortcut, independent of db_backend
    # so it can still be used against Snowflake during build/test — but must be
    # turned off (or simply unset) before any real deployment.
    allow_dev_login: bool = os.getenv("ALLOW_DEV_LOGIN", "false").lower() == "true"

    # Comma-separated list of allowed frontend origins, e.g.
    # "https://dealership-inventory.vercel.app,http://localhost:3100"
    cors_origins: list[str] = [
        o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:3100").split(",") if o.strip()
    ]
    jwt_secret: str = os.getenv("JWT_SECRET", "dev-secret-change-me")
    jwt_algorithm: str = "HS256"
    jwt_expires_minutes: int = 60 * 12

    class Config:
        env_file = ".env"


settings = Settings()
