import logging
from main import main

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_application():
    """Main function to run the application."""
    try:
        main()
    except Exception as e:
        logger.exception("An unexpected error occurred: %s", e)


if __name__ == "__main__":
    run_application()
