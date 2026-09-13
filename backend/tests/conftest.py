import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.database.mysql import db_manager


@pytest_asyncio.fixture(autouse=True)
async def setup_test_db():
    db_manager.use_sqlite = True
    await db_manager.connect()
    yield
    await db_manager.disconnect()


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
