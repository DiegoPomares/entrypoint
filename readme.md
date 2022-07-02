# Entrypoint

An entrypoint script for docker that renders files using Jinja2.

The configuration file consists of key value pairs specifying template files and destinations. Template paths are relative to the configuration file path, but they can also be absolute. Example:

```yaml
templates/nginx.conf.j2: /etc/nginx/nginx.conf
templates/ntp.conf.j2: /etc/ntp.conf
```

Multiple YAML property files can be specified with the `--props` option, they are merged and exposed to the Jinja2 engine in the `props` object. Environment variables are exposed in the `env` object.

## Usage

```bash
# Basic usage
./entrypoint.py --config config.yml -- apachectl -D FOREGROUND

# Using override to write files every time, useful when the templates
# take values from environment variables
./entrypoint.py --config config.yml --override -- nginx

# Combine multiple property files
./entrypoint.py --config config.yml --props common.yml production.yml -- /opt/my_app/start.sh

# Just print the rendered files
./entrypoint.py --config config.yml --dry-run
```
