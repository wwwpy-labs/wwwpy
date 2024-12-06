import os
import logging
from pathlib import Path


async def main(rootpath, invocation_dir, args):
    from wwwpy.common.designer import log_emit
    def emit(msg: str):
        print(msg)
        from js import console
        console.log(msg)

    log_emit.add_once(emit)
    log_emit.warning_to_log()
    logging.getLogger().setLevel(logging.DEBUG)
    # from wwwpy.remote.designer import log_redirect
    # log_redirect.redirect_logging()

    from js import console
    console.log(f'main({rootpath}, {invocation_dir}, {args})')
    from wwwpy.common.tree import print_tree
    print_tree('/wwwpy_bundle')

    Path('/wwwpy_bundle/pytest.ini').write_text("[pytest]\n"
                                                "asyncio_mode = auto")
    from wwwpy.remote import micropip_install
    await micropip_install('pytest==7.2.2')  # didn't work with update to 8.1.1
    await micropip_install('pytest-asyncio')
    await micropip_install('pytest-xvirt')
    import wwwpy.common.designer as des
    for package in des.pypi_packages:
        await micropip_install(package)
    import pytest
    print('-=-' * 20 + 'pytest imported')

    os.chdir(invocation_dir)
    pytest.main(args)
