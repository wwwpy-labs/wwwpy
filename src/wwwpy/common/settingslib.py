from pathlib import Path
import logging
import configparser

logger = logging.getLogger(__name__)


class Settings:
    def __init__(self):
        self._config = configparser.ConfigParser()

    def load(self, ini_file: Path):
        logger.debug(f'Loading settings from {ini_file}')
        self._config.read(ini_file)

    @property
    def hotreload_self(self) -> bool:
        return self._config.getboolean('general', 'hotreload_self', fallback=False)

    @property
    def open_url_code(self) -> str:
        return self._config.get('general', 'open_url_code', fallback='')
