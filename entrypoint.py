#!/usr/bin/env python

import argparse
import os
import textwrap
import sys
from pathlib import Path
from typing import Any, Dict, List, NoReturn

import jinja2
import yaml


def get_abs_path_for_file_relative_to_config_file(config_file:str, file_path:str, *, prefix:str="") -> str:
    if prefix:
        config_file_path = Path(config_file)
        if config_file_path.is_absolute():
            config_file_path = config_file_path.relative_to(config_file_path.anchor)
        basedir = Path(prefix) / config_file_path.parent
    else:
        basedir = Path(config_file).absolute().parent

    final_path = Path(basedir) / file_path
    return str(final_path)


def read_config_file(config_path:str) -> Dict[str, str]:
    with open(config_path) as fh:
        config:Dict = yaml.load(fh, yaml.Loader)

    return {
        get_abs_path_for_file_relative_to_config_file(config_path, template_src): template_dst
        for template_src, template_dst in config.items()
    }


def read_properties_from_files(*property_files:str) -> Dict:
    props = {}
    for file_path in property_files:
        with open(file_path) as fh:
            contents:Dict = yaml.load(fh, yaml.Loader)
            props.update(contents)

    return props


def render_template(file_path:str, **properties:Any) -> str:
    with open(file_path) as fh:
        return jinja2.Template(fh.read()).render({
            "env": os.environ,
            "props": properties,
        })


def render_files(template_config:Dict[str, str], props:Dict) -> Dict[str, str]:
    output = {}
    for template_src, template_dst in template_config.items():
        output[template_dst] = render_template(template_src, **props)

    return output


def write_file(file_path:str, contents:str, overwrite:bool=False) -> bool:
    if not overwrite and Path(file_path).exists():
        return False

    with open(file_path, "w") as fh:
        fh.write(contents)


def write_rendered_templates(rendered_files, dry_run:bool, overwrite:bool) -> None:
    print("Rendering templates")

    for path, contents in rendered_files.items():
        print(f"{path}: ", end="")
        if dry_run:
            print("\n", textwrap.indent(contents, "  "), "\n", sep="")
            continue

        if write_file(path, contents, overwrite):
            print("OK")
        else:
            print("Skipped")


def launch_command(*cmd_args) -> NoReturn:
    print("Launching:", " ".join(cmd_args))
    os.execvp(cmd_args[0], cmd_args)


def main(args:argparse.Namespace, *cmd_args:str) -> None:
    if args.config:
        config = read_config_file(args.config)
        props = read_properties_from_files(*args.props)
        rendered_files = render_files(config, props)

        write_rendered_templates(rendered_files, args.dry_run, args.overwrite)
    else:
        print("No templates to render")

    if cmd_args and not args.dry_run:
        launch_command(*cmd_args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter,
        description=textwrap.dedent("""
        Docker entrypoint script that renders jinja2 templates and writes them to a destination.
        The configuration file is a YAML file with an object where key/values represent:

        TEMPLATE_FILE_PATH: DESTINATION_PATH

        Template paths are relative to the configuration file.
        Use '--' to specify a command that will be run after the rendering is complete.

        Example usage:
          ./entrypoint.py --config prod.conf -- apachectl -D FOREGROUND
        """).strip())
    parser.add_argument("--config", default="", type=str,
        help="Template configuration file (default: %(default)s)")
    parser.add_argument("--props", metavar="PROPERTY_FILE", type=str, nargs="*", default=tuple(),
        help="YAML files with properties for the Jinja2 engine, they will be merged into the 'props' object")
    parser.add_argument("--dry-run", action="store_true",
        help="Print the rendered templates instead of writing them to their destinations")
    parser.add_argument("--overwrite", action="store_true",
        help="Overwrite destination files if they already exist")
    parser.add_argument("cmd_args", metavar="CMD_ARGS", nargs=argparse.REMAINDER,
        help="""Specify a command with after '--' to run with an EXEC call after the rendering is complete""")

    args = parser.parse_args()

    cmd_args:List = args.cmd_args
    if cmd_args and cmd_args[0] != "--":
        if "--" not in cmd_args:
            invalid_args = cmd_args
        else:
            dd_index = cmd_args.index("--")
            invalid_args = cmd_args[:dd_index]

        print("Error, invalid command line arguments:", " ".join(invalid_args))
        sys.exit(1)

    main(args, *cmd_args[1:])
