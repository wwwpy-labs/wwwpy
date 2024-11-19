import subprocess


def install_requirements():
    subprocess.run(['uv', 'pip', 'install', '-e', '.[all]'], check=True)
    subprocess.run(['playwright', 'install-deps', 'chromium'], check=True)


if __name__ == "__main__":
    install_requirements()
