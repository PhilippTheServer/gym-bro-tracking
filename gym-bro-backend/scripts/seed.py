"""Import the vendored exercise catalogue into the database.

Run on every container start. The import is reconciling, not destructive: exercises
already present are enriched in place and nothing is ever deleted, so templates and
finished workouts keep pointing at the same rows.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.domain.exercise_catalog import load_catalog
from app.repositories.exercise_repository import ExerciseRepository
from app.use_cases.exercise.import_catalog import ImportCatalogUseCase, ImportSummary


async def seed(database_url: str) -> ImportSummary:
    """
    Arg: database_url - async SQLAlchemy URL of the target database.
    Operation: loads the catalogue and reconciles it against the stored exercise library.
    Return: ImportSummary describing what the run changed.
    """
    engine = create_async_engine(database_url, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as session:
        use_case = ImportCatalogUseCase(ExerciseRepository(session))
        summary = await use_case.execute(load_catalog())

    await engine.dispose()
    return summary


if __name__ == "__main__":
    settings = get_settings()
    result = asyncio.run(seed(settings.database_url))
    print(
        f"Exercise catalogue imported: {result.inserted} new, "
        f"{result.updated} updated, {result.unchanged} unchanged."
    )
