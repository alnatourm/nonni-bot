import logging
import os

from app.config import (
    settings,
    validate_settings,
)

from app.database import init_database
from app.telegram_bot import create_application


async def post_init(application):
    await init_database()


def main():

    validate_settings()

    os.makedirs(
        "data",
        exist_ok=True,
    )

    logging.basicConfig(
        level=getattr(
            logging,
            settings.log_level.upper(),
            logging.INFO,
        ),
        format=(
            "%(asctime)s "
            "%(levelname)s "
            "%(name)s "
            "%(message)s"
        ),
    )

    application = create_application()

    application.post_init = post_init

    logging.info(
        "Starting Nonni 2.0..."
    )

    application.run_polling(
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()
