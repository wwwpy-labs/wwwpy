import os

_INITIAL = set(globals())

PLAYWRIGHT_PATCH_TIMEOUT_MILLIS = 45000
PLAYWRIGHT_HEADFUL = False

_NEW = set(globals()) - _INITIAL
_NEW.remove('_INITIAL')
try:
    import wwwpy_user_conf

    # list all the local custom variables and copy them (if they exists from wwwpy_user_conf)
    for key in _NEW:
        if hasattr(wwwpy_user_conf, key):
            value = getattr(wwwpy_user_conf, key)
            globals()[key] = value
        else:
            env_value = os.environ.get(key)
            if env_value is not None:
                globals()[key] = env_value

except ModuleNotFoundError:
    import logging

    logger = logging.getLogger(__name__)
    logger.info("No local wwwpy_user_conf.py file found. Using default values.")
