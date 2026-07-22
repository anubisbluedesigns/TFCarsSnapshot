from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from .config import settings


def _build_engine():
    if settings.db_backend == "snowflake":
        from cryptography.hazmat.primitives import serialization
        from snowflake.sqlalchemy import URL

        if settings.snowflake_private_key_b64:
            # Render (and most PaaS hosts) don't have a good place to drop a
            # .pem file, so in production the key is pasted as one base64 env
            # var instead of a file path.
            import base64

            pem_bytes = base64.b64decode(settings.snowflake_private_key_b64)
        else:
            with open(settings.snowflake_private_key_path, "rb") as f:
                pem_bytes = f.read()
        p_key = serialization.load_pem_private_key(pem_bytes, password=None)
        pkb = p_key.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        url = URL(
            account=settings.snowflake_account,
            user=settings.snowflake_user,
            warehouse=settings.snowflake_warehouse,
            database=settings.snowflake_database,
            schema=settings.snowflake_schema,
            role=settings.snowflake_role,
        )
        # Some networks (this one included, per TFCarsSoldDash's existing config)
        # intermittently fail Snowflake's OCSP cert-revocation check with a false
        # "certificate is revoked" error. insecure_mode skips that check — the
        # connection is still TLS-encrypted, it just doesn't verify revocation.
        return create_engine(
            url, connect_args={"private_key": pkb, "insecure_mode": settings.snowflake_insecure_mode}
        )

    # local dev default
    return create_engine(
        f"sqlite:///{settings.sqlite_path}",
        connect_args={"check_same_thread": False},
    )


engine = _build_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
