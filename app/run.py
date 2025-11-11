"""
项目启动入口：`python app/run.py`
"""

from __future__ import annotations

import sys
from pathlib import Path

import uvicorn
from uvicorn.config import LOGGING_CONFIG

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def configure_logging() -> None:
    # 统一日志格式，方便排查问题
    LOGGING_CONFIG["formatters"]["default"]["fmt"] = "%(asctime)s - %(levelname)s - %(message)s"
    LOGGING_CONFIG["formatters"]["default"]["datefmt"] = "%Y-%m-%d %H:%M:%S"
    LOGGING_CONFIG["formatters"]["access"][
        "fmt"
    ] = '%(asctime)s - %(levelname)s - %(client_addr)s - "%(request_line)s" %(status_code)s'
    LOGGING_CONFIG["formatters"]["access"]["datefmt"] = "%Y-%m-%d %H:%M:%S"


def main() -> None:
    configure_logging()
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=9999,
        reload=True,
        log_config=LOGGING_CONFIG,
    )


if __name__ == "__main__":
    main()
