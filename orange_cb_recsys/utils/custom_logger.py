import logging
from typing import Optional, Dict

from colorama import Fore, Back, Style


class ColoredFormatter(logging.Formatter):
    """Colored log formatter."""

    def __init__(self, *args, colors: Optional[Dict[str, str]] = None, **kwargs) -> None:
        """Initialize the formatter with specified format strings."""

        super().__init__(*args, **kwargs)

        self.colors = colors if colors else {}

    def format(self, record) -> str:
        """Format the specified record as text."""

        record.color = self.colors.get(record.levelname, '')
        record.reset = Style.RESET_ALL

        return super().format(record)


formatter = ColoredFormatter(
    "\r{color}{levelname}{reset} - {message} ({filename}:{lineno})",
    style='{',
    colors={
        'DEBUG': Fore.CYAN,
        'INFO': Fore.RESET,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.BLACK + Back.RED + Style.BRIGHT,
    }
)


def getCustomLogger(name: str):
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger
