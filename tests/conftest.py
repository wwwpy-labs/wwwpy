pytest_plugins = ['pytester']

import logging


def pytest_configure():
    packages = ['tests', 'wwwpy', 'common', 'remote', 'server']
    for log_name in packages:
        logging.getLogger(log_name).setLevel(logging.DEBUG)
