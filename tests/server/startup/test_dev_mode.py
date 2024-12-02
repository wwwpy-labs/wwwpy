from wwwpy.server.tcp_port import find_port


def test_start_dev_mode__empty_folder(tmp_path):
    from wwwpy.server.convention import start_default
    start_default(tmp_path, find_port(), dev_mode=True)
    assert True
