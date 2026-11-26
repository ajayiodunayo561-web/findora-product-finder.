"""Findora Product Finder — entrypoint. Stage 1: boots config + DB."""
import asyncio
import logging

from config import get_settings
from database.db import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)
log = logging.getLogger("findora")


async def main() -> None:
    settings = get_settings()
    log.info("Booting Findora (mode=%s)", settings.deploy_mode)
    await init_db()
    log.info("Database ready: %s", settings.sqlalchemy_url.split("://", 1)[0])
    log.info("Stage 1 OK — handlers will be wired in Stage 2.")
    await asyncio.Event().wait()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        log.info("Shutdown requested.")
