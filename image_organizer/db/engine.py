from pathlib import Path

from sqlalchemy import create_engine

db_path = str(Path('./images.db').absolute())
engine = create_engine(
    f'sqlite+pysqlite:///{db_path}'
)
