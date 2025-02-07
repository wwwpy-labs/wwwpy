import os
import logging

logger = logging.getLogger(__name__)


def is_github():
    getenv = os.getenv('GITHUB_ACTIONS')
    return getenv == 'true'


def timeout_multiplier():
    multiplier = 15 if is_github() else 1
    return multiplier


logger.debug(f'timeout_multiplier={timeout_multiplier()}')
