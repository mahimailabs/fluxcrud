from unittest.mock import MagicMock, patch

import pytest

from fluxcrud.database.drivers import Database


@pytest.mark.asyncio
async def test_database_pooling_config():
    db = Database()

    with patch("fluxcrud.database.drivers.create_async_engine") as mock_create_engine:
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        db.init(
            "postgresql+asyncpg://user:pass@localhost/db",
            pool_size=5,
            max_overflow=2,
            pool_recycle=1800,
            pool_timeout=10,
        )

        mock_create_engine.assert_called_once()
        _, kwargs = mock_create_engine.call_args

        assert kwargs["pool_size"] == 5
        assert kwargs["max_overflow"] == 2
        assert kwargs["pool_recycle"] == 1800
        assert kwargs["pool_timeout"] == 10


@pytest.mark.asyncio
async def test_database_pooling_default_config():
    db = Database()

    with patch("fluxcrud.database.drivers.create_async_engine") as mock_create_engine:
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        db.init("postgresql+asyncpg://user:pass@localhost/db")

        mock_create_engine.assert_called_once()
        _, kwargs = mock_create_engine.call_args

        assert kwargs["pool_size"] == 20
        assert kwargs["max_overflow"] == 10
        assert kwargs["pool_recycle"] == 3600
        assert kwargs["pool_timeout"] == 30
