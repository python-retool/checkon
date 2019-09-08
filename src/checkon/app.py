import contextlib
import os
import pathlib
import shlex
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
    project_tempdir = pathlib.Path(tempfile.TemporaryDirectory().name)
    result_path = project_tempdir / "result.json"
    results_dir = pathlib.Path(tempfile.TemporaryDirectory().name)

    print(1)
    subprocess.run(["git", "clone", str(project_url), str(project_tempdir)], check=True)

    # Create the envs and install deps.
    subprocess.run(
        [sys.executable, "-m", "tox", "--notest", "-c", str(project_tempdir)],
        cwd=str(project_tempdir),
        check=True,
    )

    # Install the injection into each venv
    args = [
        sys.executable,
        "-m",
        "tox",
        "--run-command",
        "python -m pip install " + shlex.quote(str(inject)),
    ]
    print(" ".join(args))
    subprocess.run(args, cwd=str(project_tempdir))

    # Get environment names.
    envnames = (
        subprocess.run(
            [sys.executable, "-m", "tox", "-l"],
            cwd=str(project_tempdir),
            capture_output=True,
        )
        .stdout.decode()
        .splitlines()
    )

    for envname in envnames:
        # Run the environment.
        output_file = results_dir / f"{envname}.xml"
        subprocess.run(
            [
                sys.executable,
                "-m",
                "tox",
                "--result-json",
                str(result_path),
                "-e",
                envname,
            ],
            cwd=str(project_tempdir),
            check=False,
            env={
                "TOX_TESTENV_PASSENV": "PYTEST_ADDOPTS",
                "PYTEST_ADDOPTS": f"--tb=long --junitxml={output_file}",
                **os.environ,
            },
        )
    return str(results_dir)
