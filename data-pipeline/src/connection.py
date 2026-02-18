"""
Snowflake connection for KAREO.TALISMANSOLUTIONS.
Uses same env vars as Tebra-Snowflake: SNOWFLAKE_URL, USER, PASSWORD, DATABASE, SCHEMA.
"""
import os
from pathlib import Path
from urllib.parse import urlparse

_root = Path(__file__).resolve().parent.parent
_dotenv = _root / ".env"
if _dotenv.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(_dotenv)
    except ImportError:
        pass


def _account_from_url(url: str) -> str:
    parsed = urlparse(url)
    host = (parsed.netloc or parsed.path).strip().lower()
    if not host:
        raise ValueError(f"Could not get host from SNOWFLAKE_URL: {url!r}")
    suffix = ".snowflakecomputing.com"
    if host.endswith(suffix):
        return host[: -len(suffix)]
    return host


def get_connection():
    """Return a Snowflake connection (KAREO.TALISMANSOLUTIONS)."""
    import snowflake.connector

    url = os.environ.get("SNOWFLAKE_URL", "").strip()
    account = os.environ.get("SNOWFLAKE_ACCOUNT", "").strip()
    user = os.environ.get("SNOWFLAKE_USER")
    password = os.environ.get("SNOWFLAKE_PASSWORD")
    role = os.environ.get("SNOWFLAKE_ROLE")
    warehouse = os.environ.get("SNOWFLAKE_WAREHOUSE")
    database = os.environ.get("SNOWFLAKE_DATABASE")
    schema = os.environ.get("SNOWFLAKE_SCHEMA")

    if url:
        account = _account_from_url(url)
    if not account or not user or not password:
        raise ValueError(
            "Set SNOWFLAKE_URL (or SNOWFLAKE_ACCOUNT), SNOWFLAKE_USER, SNOWFLAKE_PASSWORD in .env"
        )

    return snowflake.connector.connect(
        account=account,
        user=user,
        password=password,
        role=role or None,
        warehouse=warehouse or None,
        database=database or None,
        schema=schema or None,
    )
