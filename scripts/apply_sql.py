import argparse
import asyncio
import pathlib
import sys

import asyncpg

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.settings import get_settings  # noqa: E402


async def execute_sql(path: pathlib.Path) -> None:
    if not path.exists():
        raise FileNotFoundError(path)
    sql = path.read_text()
    settings = get_settings()
    dsn = settings.database_url.replace("+asyncpg", "")
    conn = await asyncpg.connect(dsn)
    try:
        await conn.execute(sql)
        print(f"Applied {path}")
    finally:
        await conn.close()


async def main() -> None:
    parser = argparse.ArgumentParser(description="Apply raw SQL against configured database")
    parser.add_argument("files", nargs="+", type=pathlib.Path, help="SQL files to execute")
    args = parser.parse_args()
    for sql_file in args.files:
        await execute_sql(sql_file)


if __name__ == "__main__":
    asyncio.run(main())
