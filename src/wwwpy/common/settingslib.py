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

    @property
    def log_level(self) -> dict[str, str]:
        if not self._config.has_section('log_level'):
            return {}
        return dict(self._config.items('log_level'))
