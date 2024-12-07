import logging

from wwwpy.common.loglib import translate_names


def test_translate_names():
    result = translate_names({'mod1.mod2': 'DEBUG', 'mod3': 'INFO'})
    assert result == {'mod1.mod2': logging.DEBUG, 'mod3': logging.INFO}


def test_translate_unrecognized():
    result = translate_names({'mod1.mod2': 'DEBUG', 'mod3': 'INFO', 'mod4': 'FOO'})
    assert result == {'mod1.mod2': logging.DEBUG, 'mod3': logging.INFO}
