# Command Line Usage

The `wwwpy` command line interface provides various options to run and configure your wwwpy project.

## Usage

```sh
$ wwwpy --help
usage: wwwpy [-h] [--directory DIRECTORY] [--port PORT] [dev]

positional arguments:
  dev                   Run in development mode

optional arguments:
  -h, --help            show this help message and exit
  --directory DIRECTORY, -d DIRECTORY
                        set the root path for the project (default: current directory)
  --port PORT           bind to this port (default: 8000)
```

## Positional Arguments

- `dev`: Run the wwwpy server in development mode. This mode is useful for development as it provides features like hot-reloading and detailed logging.

If the `dev` argument is not provided, the server runs in production mode. In production mode, development features such as hot-reloading and the editing toolbox are not active.

## Optional Arguments

- `-h, --help`: Show the help message and exit. This option provides information about the usage of the `wwwpy` command and its available options.

- `--directory DIRECTORY, -d DIRECTORY`: Set the root path for the project. By default, it uses the current directory. This option allows you to specify a different directory as the root of your wwwpy project.

- `--port PORT`: Bind the server to the specified port. The default port is 8000. Use this option to run the server on a different port if needed.

## Examples

### Running in Development Mode

To start the wwwpy server in development mode, simply use the following command:

```sh
wwwpy dev
```

### Specifying a Project Directory

To run the wwwpy server with a specific project directory, use the `--directory` or `-d` option:

```sh
wwwpy --directory /path/to/project dev
```

### Specifying a Port

To run the wwwpy server on a different port, use the `--port` option:

```sh
wwwpy --port 8080 dev
```

You can combine these options as needed to configure the server according to your requirements.
