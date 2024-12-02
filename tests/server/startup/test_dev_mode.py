from wwwpy.server.tcp_port import find_port


def test_start_dev_mode__empty_folder(tmp_path):
    from wwwpy.server.conv import start_default
    start_default(find_port(), tmp_path, dev_mode=True)
    assert True
