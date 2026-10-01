"""Generic async repository providing basic CRUD operations."""

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Base


class BaseRepository[ModelT: Base]:
    """Abstract base repository wiring a SQLAlchemy model to an async session."""

    model: type[ModelT]

    def __init__(self, session: AsyncSession) -> None:
        """
        Arg: session - async SQLAlchemy session for the current request.
        Operation: stores the session as a protected attribute.
        Return: BaseRepository instance.
        """
        self.session = session

    async def get(self, id: uuid.UUID) -> ModelT | None:
        """
        Arg: id - primary key UUID.
        Operation: fetches the entity by primary key using the session cache or database.
        Return: the entity if found, otherwise None.
        """
        return await self.session.get(self.model, id)

    async def list(self, **filters: Any) -> list[ModelT]:
        """
        Arg: filters - keyword arguments mapped to model column equality conditions.
        Operation: constructs and executes a SELECT with the given filters applied.
        Return: list of matching entities.
        """
        query = select(self.model)
        for attribute, value in filters.items():
            query = query.where(getattr(self.model, attribute) == value)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    def add(self, obj: ModelT) -> None:
        """
        Arg: obj - entity instance to persist.
        Operation: stages the entity for insertion without flushing, so a bulk import can
                   issue one round trip at commit instead of one per row.
        Return: None.
        """
        self.session.add(obj)

    async def create(self, obj: ModelT) -> ModelT:
        """
        Arg: obj - entity instance to persist.
        Operation: adds the entity to the session, flushes to obtain a database-assigned ID,
                   and refreshes the instance with server-generated values.
        Return: the persisted entity instance.
        """
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def delete(self, obj: ModelT) -> None:
        """
        Arg: obj - entity instance to remove.
        Operation: marks the entity for deletion and flushes within the current transaction.
        Return: None.
        """
        await self.session.delete(obj)
        await self.session.flush()

    async def commit(self) -> None:
        """
        Arg: none.
        Operation: commits the current transaction, making all pending changes durable.
        Return: None.
        """
        await self.session.commit()
