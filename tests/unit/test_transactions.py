import pytest
from sqlalchemy import text

from fluxcrud.transactions.manager import TransactionManager


@pytest.mark.asyncio
async def test_transaction_manager_commit(session):
    manager = TransactionManager(session)

    async with manager.transaction() as txn_session:
        await txn_session.execute(text("SELECT 1"))

    assert not session.in_transaction()


@pytest.mark.asyncio
async def test_transaction_manager_nested(session):
    manager = TransactionManager(session)

    async with session.begin():
        async with manager.transaction() as txn_session:
            await txn_session.execute(text("SELECT 1"))

    assert not session.in_transaction()
