import asyncio
from collections import defaultdict
from pathlib import Path
import sys

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.core.database import get_db  # noqa: E402
from app.core.redis import get_redis  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.main import create_app  # noqa: E402
from app.models.base import Base  # noqa: E402
from app.models.menu import Menu, MenuType  # noqa: E402
from app.models.role import Permission, Role, RoleMenu  # noqa: E402
from app.models.user import User  # noqa: E402


class FakeRedis:
    def __init__(self) -> None:
        self.counters = defaultdict(int)
        self.hashes: dict[str, dict] = {}

    async def incr(self, key: str) -> int:
        self.counters[key] += 1
        return self.counters[key]

    async def expire(self, key: str, seconds: int) -> None:  # pragma: no cover - noop
        _ = (key, seconds)

    async def expireat(self, key: str, timestamp: int) -> None:  # pragma: no cover - noop
        _ = (key, timestamp)

    async def hset(self, key: str, mapping: dict) -> None:
        self.hashes[key] = mapping

    async def delete(self, key: str) -> None:
        self.hashes.pop(key, None)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def async_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="session")
async def session_factory(async_engine):
    factory = async_sessionmaker(async_engine, expire_on_commit=False, class_=AsyncSession)

    async with factory() as session:
        admin_role = Role(id=1, code="admin", name="Administrator")
        test_role = Role(id=2, code="test", name="Tester")

        perm_all = Permission(id=1, namespace="*", resource="*", action="*", label="All")
        perm_create = Permission(id=2, namespace="example", resource="dialog", action="create")
        perm_delete = Permission(id=3, namespace="example", resource="dialog", action="delete")
        admin_role.permissions.extend([perm_all])
        test_role.permissions.extend([perm_create, perm_delete])

        admin_user = User(
            id=1,
            username="admin",
            email="admin@example.com",
            password_hash=hash_password("admin"),
            is_superuser=True,
            is_active=True,
        )
        tester = User(
            id=2,
            username="test",
            email="test@example.com",
            password_hash=hash_password("test"),
            is_superuser=False,
            is_active=True,
        )

        admin_user.roles.append(admin_role)
        tester.roles.append(test_role)

        dashboard = Menu(
            id=1,
            name="Dashboard",
            title="Dashboard",
            title_i18n="router.dashboard",
            path="/dashboard",
            component="#",
            order=1,
            type=MenuType.DIRECTORY,
        )
        analysis = Menu(
            id=2,
            parent_id=1,
            name="Analysis",
            title="Analysis",
            title_i18n="router.analysis",
            path="analysis",
            component="views/Dashboard/Analysis",
            order=1,
            type=MenuType.ROUTE,
        )

        session.add_all(
            [
                admin_role,
                test_role,
                perm_all,
                perm_create,
                perm_delete,
                admin_user,
                tester,
                dashboard,
                analysis,
                RoleMenu(id=1, role_id=1, menu_id=1),
                RoleMenu(id=2, role_id=1, menu_id=2),
            ]
        )
        await session.commit()

    return factory


@pytest_asyncio.fixture
async def test_app(session_factory):
    app = create_app()
    fake_redis = FakeRedis()

    async def _override_get_db():
        async with session_factory() as session:
            yield session

    async def _override_get_redis():
        yield fake_redis

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_redis] = _override_get_redis
    yield app
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client(test_app):
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
