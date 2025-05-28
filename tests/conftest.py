pytest_plugins = ['pytester']

import logging


def pytest_configure():
    packages = ['tests', 'wwwpy', 'common', 'remote', 'server']
    for log_name in packages:
        logging.getLogger(log_name).setLevel(logging.DEBUG)


def pytest_report_from_serializable(config, data):
    replace_pair = [
        (
            'File "/wwwpy_bundle/tests/',
            'File "tests/'
        ),
        (
            'File "/wwwpy_bundle/wwwpy/',
            'File "src/wwwpy/'
        ),
    ]

    def _replace_in_string(s: str) -> str:
        for old, new in replace_pair:
            s = s.replace(old, new)
        return s

    sections = data.get('sections', [])
    for section in sections:
        name: str = section[0]
        content: str = section[1]
        new_content = _replace_in_string(content)
        if new_content != content:
            section[1] = f'This stderr was modified by {__file__}\n{new_content}'
