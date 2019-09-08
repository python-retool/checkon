import contextlib
import pathlib
import site
import subprocess
import sys
import tempfile
import textwrap
import typing as t

import attr
import hyperlink
import pyrsistent


@attr.dataclass(frozen=True)
class Project:
    test_command: t.Sequence[str] = attr.ib(
        default=["tox"], converter=pyrsistent.freeze
    )


@attr.dataclass(frozen=True)
class GitRepo:
    url: hyperlink.URL = attr.ib(converter=hyperlink.URL.from_text)
    project: Project


@contextlib.contextmanager
def install_hooks(module: str):
    """

    Args:
        module: The module to insert.

    """
    path = pathlib.Path(site.USER_SITE) / "usercustomize.py"
    try:
        original = path.read_text()
    except FileNotFoundError:
        original = None

    module = repr(str(module))
    text = textwrap.dedent(
        f"""\
    import os
    import sys

    def hook(*args):
        with open('/tmp/checkon/' + str(os.getpid())) as f:
            f.write(str(args))

    sys.excepthook = hook


    sys.path.insert(0, {module})
    """
    )
    path.write_text(text)
    try:
        yield
    finally:
        pass
        if original is None:
            path.unlink()
        else:
            path.write_text(original)


def run(project_url, inject: str):
    dir = pathlib.Path(tempfile.TemporaryDirectory().name)

    subprocess.run(["git", "clone", str(project_url), str(dir)], check=True)
    dir = "/tmp/tmp0x2e4339"
    with install_hooks(inject):
        proc = subprocess.run([sys.executable, "-m", "tox"], cwd=str(dir))

    return proc.returncode
