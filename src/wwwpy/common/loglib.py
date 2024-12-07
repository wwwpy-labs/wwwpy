import logging


def set_log_level(log_level: dict[str, str]):
    tr = translate_names(log_level)
    for module, level in tr.items():
        logging.getLogger(module).setLevel(level)


def translate_names(log_level):
    translated = {}
    for module, level in log_level.items():
        name = logging.getLevelName(level)
        if isinstance(name, int):
            translated[module] = name
    return translated
