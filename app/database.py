from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.core.base import Base  # noqa: F401 – re-exported for test conftest compatibility

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Register all models with Base.metadata
import app.models.user  # noqa: F401, E402
import app.models.organization  # noqa: F401, E402
import app.models.project  # noqa: F401, E402
import app.models.issue  # noqa: F401, E402
import app.models.comment  # noqa: F401, E402
import app.models.activity_log  # noqa: F401, E402
import app.models.label  # noqa: F401, E402


def create_tables() -> None:
    Base.metadata.create_all(bind=engine)
