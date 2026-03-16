import certifi

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config import get_settings

_client: AsyncIOMotorClient | None = None


def get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        settings = get_settings()
        client_options: dict[str, object] = {
            "serverSelectionTimeoutMS": 30000,
        }

        tls_mode = settings.mongo_tls_mode
        should_use_tls_bundle = tls_mode == "enabled"
        if tls_mode == "auto":
            should_use_tls_bundle = settings.mongo_uri.startswith("mongodb+srv://") or "mongodb.net" in settings.mongo_uri

        if should_use_tls_bundle:
            client_options["tls"] = True
            client_options["tlsCAFile"] = settings.mongo_tls_ca_file or certifi.where()

        _client = AsyncIOMotorClient(settings.mongo_uri, **client_options)
    return _client


def get_db() -> AsyncIOMotorDatabase:
    settings = get_settings()
    return get_client()[settings.mongo_db_name]


async def ping_database() -> bool:
    db = get_db()
    result = await db.command("ping")
    return bool(result.get("ok"))