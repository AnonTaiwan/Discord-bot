import os
from contextlib import contextmanager
from typing import Iterator
from sqlmodel import SQLModel, Session, create_engine
from alembic.config import Config
from alembic import command
from internal.config import CONFIG
from internal import utils

DB_FILENAME = CONFIG.database.filename
DATABASE_PATH = utils.ROOT_DIR / DB_FILENAME
DATABASE_URL = f"sqlite:///{DATABASE_PATH.as_posix()}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


def init_db() -> None:
    """Create all SQLModel tables if they do not exist yet."""
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    SQLModel.metadata.create_all(engine)


def run_migrations() -> None:
    # Resolve any legacy chat migrations in the database
    if DATABASE_PATH.exists():
        import sqlite3
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            # Check if alembic_version table exists and get its value
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='alembic_version'")
            if cursor.fetchone():
                cursor.execute("SELECT version_num FROM alembic_version")
                row = cursor.fetchone()
                if row:
                    current_ver = row[0]
                    # If the database is on one of the reverted/removed chat migrations, reset it to the last stable migration
                    if current_ver in ("3516d5f513d1", "b02ad4dee518"):
                        print(f"Detected reverted migration version '{current_ver}' in database. Performing self-healing clean up...")
                        # Drop the chatmessage table if it exists
                        cursor.execute("DROP TABLE IF EXISTS chatmessage")
                        # Update the alembic version to the last known stable version (afd97277f96b)
                        cursor.execute("UPDATE alembic_version SET version_num = 'afd97277f96b'")
                        conn.commit()
                        print("Self-healing clean up completed successfully.")
            conn.close()
        except Exception as e:
            print(f"Warning: Failed to perform database self-healing checks: {e}")

    ini_path = os.path.join(utils.ROOT_DIR, "alembic.ini")

    alembic_cfg = Config(ini_path)

    print("Running database migrations...")
    command.upgrade(alembic_cfg, "head")
    print("Migrations complete!")


@contextmanager
def get_session() -> Iterator[Session]:
    """Yield a SQLModel session bound to the shared engine."""
    session = Session(engine, expire_on_commit=False)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
