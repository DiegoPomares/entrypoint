import os
import pathlib
import textwrap

import pytest

from entrypoint import (
    get_abs_path_for_file_relative_to_config_file,
    read_config_file,
    read_properties_from_files,
    render_files,
    render_template,
    write_rendered_templates,
)

TEMPLATE_CONFIG = {
    "test/resources/templates/example.conf.j2": "example.conf",
    "test/resources/templates/example2.conf.j2": "target.conf",
}

PROPS = {
    "prop1": "prop1 SET"
}

RENDERED_TEMPLATES = {
    "example.conf": textwrap.dedent("""
        This is an example template

        Environment variable ENV1: ENV1 SET
        Environment variable ENV2: MISSING

        Property prop1: prop1 SET
        Property prop2: prop2 DEFAULT
        """).strip(),
    "target.conf": textwrap.dedent("""
        This is another example template

        Environment variable ENV1: ENV1 SET

        Property prop1: prop1 set
        """).strip(),
}


@pytest.mark.parametrize(
    "config_file_path,template_path,result",
    [
        ("config.yml", "example.conf.j2", "/opt/example.conf.j2"),
        ("dir/config.yml", "example.conf.j2", "/opt/dir/example.conf.j2"),
        ("/tmp/config.yml", "example.conf.j2", "/opt/tmp/example.conf.j2"),

        ("config.yml", "templates/example.conf.j2", "/opt/templates/example.conf.j2"),
        ("dir/config.yml", "templates/example.conf.j2", "/opt/dir/templates/example.conf.j2"),
        ("/tmp/config.yml", "templates/example.conf.j2", "/opt/tmp/templates/example.conf.j2"),

        ("config.yml", "/var/example.conf.j2", "/var/example.conf.j2"),
        ("dir/config.yml", "/var/example.conf.j2", "/var/example.conf.j2"),
        ("/tmp/config.yml", "/var/example.conf.j2", "/var/example.conf.j2"),
    ]
)
def test_get_path_relative_to_file(config_file_path:str, template_path:str, result:str):
    assert get_abs_path_for_file_relative_to_config_file(config_file_path, template_path, prefix="/opt") == result


def test_read_template_config_file():
    template_config_file_path = "test/resources/config.yml"
    template_config_file_abspath = os.path.abspath(template_config_file_path)
    template_basedir = os.path.dirname(template_config_file_abspath)

    assert read_config_file(template_config_file_path) == {
        os.path.join(template_basedir, "templates/example.conf.j2"): "example.conf",
        os.path.join(template_basedir, "templates/example2.conf.j2"): "example2.conf",
    }


def test_read_properties_from_files():
    props = read_properties_from_files(
        "test/resources/props/file1.yml",
        "test/resources/props/file2.yml"
    )

    assert props == {
        "prop1": "VALUE1",
        "prop2": "override",
        "prop3": "value3",
    }


def test_render_template():
    os.environ["ENV1"] = "ENV1 SET"
    template_src, template_dst = tuple(TEMPLATE_CONFIG.items())[0]
    assert render_template(template_src, **PROPS) == RENDERED_TEMPLATES[template_dst]


def test_render_files():
    os.environ["ENV1"] = "ENV1 SET"
    assert render_files(TEMPLATE_CONFIG, PROPS) == RENDERED_TEMPLATES


def rebase_test_rendered_templates(root_dir:pathlib.Path):
    return {str(root_dir / file): contents for file, contents in RENDERED_TEMPLATES.items()}


def test_write_rendered_templates(tmp_path:pathlib.Path):
    rendered_templates = rebase_test_rendered_templates(tmp_path)
    write_rendered_templates(rendered_templates, dry_run=False, overwrite=False)

    for file, contents in rendered_templates.items():
        with open(file) as fh:
            assert fh.read() == contents


def test_write_rendered_templates_without_overwrite(tmp_path:pathlib.Path):
    rendered_templates = rebase_test_rendered_templates(tmp_path)

    file_contents = "SKIP"
    existing_file = list(rendered_templates)[0]
    with open(existing_file, "w") as fh:
        fh.write(file_contents)

    write_rendered_templates(rendered_templates, dry_run=False, overwrite=False)

    with open(existing_file) as fh:
        assert fh.read() == file_contents

    for file, contents in list(rendered_templates.items())[1:]:
        with open(file) as fh:
            assert fh.read() == contents


def test_write_rendered_templates_with_overwrite(tmp_path:pathlib.Path):
    rendered_templates = rebase_test_rendered_templates(tmp_path)

    file_contents = "OVERWRITE"
    existing_file = list(rendered_templates)[0]
    with open(existing_file, "w") as fh:
        fh.write(file_contents)

    write_rendered_templates(rendered_templates, dry_run=False, overwrite=True)

    for file, contents in rendered_templates.items():
        with open(file) as fh:
            assert fh.read() == contents
