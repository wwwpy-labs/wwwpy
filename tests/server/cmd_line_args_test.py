from pathlib import Path

import pytest
import os

from wwwpy.server.__main__ import parse_arguments, Arguments

cwd_path = Path(os.getcwd())


def test_default_arguments():
    args = parse_arguments([])
    assert args == Arguments(directory=cwd_path, port=8000, dev=False)


def test_dev_mode():
    args = parse_arguments(['dev'])
    assert args == Arguments(directory=cwd_path, port=8000, dev=True)


def test_dev_mode_with_custom_port():
    args = parse_arguments(['dev', '--port', '9000'])
    assert args == Arguments(directory=cwd_path, port=9000, dev=True)


def test_custom_port():
    args = parse_arguments(['--port', '9000'])
    assert args == Arguments(directory=cwd_path, port=9000, dev=False)


def test_custom_directory_and_port_with_dev():
    args = parse_arguments(['--directory', '/tmp', '--port', '1234', 'dev'])
    assert args == Arguments(directory=Path('/tmp'), port=1234, dev=True)


def test_invalid_port():
    with pytest.raises(SystemExit):
        parse_arguments(['--port', 'invalid'])


def test_help_option():
    with pytest.raises(SystemExit):
        parse_arguments(['--help'])


def test_unknown_option():
    with pytest.raises(SystemExit):
        parse_arguments(['--unknown'])
