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
