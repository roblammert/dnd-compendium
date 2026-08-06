from collections.abc import Generator
from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from app.config import get_settings

settings = get_settings()
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args, future=True)

if settings.database_url.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def _sqlite_pragmas(dbapi_connection, _):
        cur = dbapi_connection.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.execute("PRAGMA journal_mode=WAL")
        cur.execute("PRAGMA busy_timeout=30000")
        cur.execute("PRAGMA synchronous=NORMAL")
        cur.close()

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

def get_db() -> Generator[Session, None, None]:
    with SessionLocal() as db:
        yield db


def ensure_schema_columns() -> None:
    """Apply small additive SQLite migrations for existing installations."""
    if not settings.database_url.startswith("sqlite"):
        return
    required = {
        "source_display_name": "VARCHAR(255)",
        "game_system_key": "VARCHAR(120)",
        "game_system_name": "VARCHAR(255)",
        "canonical_key": "VARCHAR(255)",
    }
    with engine.begin() as connection:
        existing = {column["name"] for column in inspect(connection).get_columns("entities")}
        for name, sql_type in required.items():
            if name not in existing:
                connection.execute(text(f"ALTER TABLE entities ADD COLUMN {name} {sql_type}"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_entities_source_display_name ON entities(source_display_name)"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_entities_game_system_key ON entities(game_system_key)"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_entities_game_system_name ON entities(game_system_name)"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_entities_canonical_key ON entities(canonical_key)"))

        # Additive sync counters for installations created before v0.7.0.
        for table_name in ("sync_runs", "sync_endpoints"):
            columns = {column["name"] for column in inspect(connection).get_columns(table_name)}
            if "records_unchanged" not in columns:
                connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN records_unchanged INTEGER NOT NULL DEFAULT 0"))

        # Existing records become grouped by their original slug. The application
        # performs a more complete name-based backfill at startup.
        connection.execute(text("UPDATE entities SET canonical_key = slug WHERE canonical_key IS NULL OR canonical_key = ''"))
