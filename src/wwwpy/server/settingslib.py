from .. import platformdirs
from ..common.settingslib import Settings


def user_settings() -> Settings:
    _user_config_path = platformdirs.user_config_path('wwwpy', roaming=True, ensure_exists=True)
    settings = Settings()
    settings.load(_user_config_path / 'settings.ini')
    return settings
