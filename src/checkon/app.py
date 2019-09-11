import contextlib
import fnmatch
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
import pkg_resources
import pyrsistent
import requests
import requirements

from . import results
from . import satests


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


def get_dependents(pypi_name, api_key, limit):

    url = f"https://libraries.io/api/pypi/{pypi_name}/dependents?api_key={api_key}&per_page={limit}"
    response = requests.get(url)

    return [
        project["repository_url"]
        for project in response.json()
        if project["repository_url"]
    ]


def resolve_inject(inject):
    """Resolve local requirements path."""
    try:
        req = list(requirements.parse(inject))[0]
    except pkg_resources.RequirementParseError:
        req = list(requirements.parse("-e" + str(inject)))[0]
    if req.path and not req.path.startswith("git+"):
        return str(pathlib.Path(req.path).resolve())
    return inject


def run_one(project_url, inject: str):
    print(project_url)

    results_dir = pathlib.Path(tempfile.TemporaryDirectory().name)
    results_dir.mkdir(exist_ok=True, parents=True)

    clone_tempdir = pathlib.Path(tempfile.TemporaryDirectory().name)
    subprocess.run(["git", "clone", str(project_url), str(clone_tempdir)], check=True)
    rev_hash = (
        subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=clone_tempdir)
        .decode()
        .strip()
    )
    project_tempdir = pathlib.Path("/tmp/checkon/" + str(rev_hash))

    if not project_tempdir.exists():
        clone_tempdir.rename(project_tempdir)

        # Create the envs and install deps.
        subprocess.run(
            [
                sys.executable,
                "-m",
                "tox",
                "--notest",
                "-c",
                str(project_tempdir),
                "--result-json",
                str(results_dir / "tox_install.json"),
            ],
            cwd=str(project_tempdir),
            check=False,
        )

    # Install the injection into each venv
    args = [
        sys.executable,
        "-m",
        "tox",
        "--run-command",
        "python -m pip install --force " + shlex.quote(str(inject)),
    ]

    subprocess.run(args, cwd=str(project_tempdir))

    # Get environment names.
    envnames = (
        subprocess.run(
            [sys.executable, "-m", "tox", "-l"],
            cwd=str(project_tempdir),
            capture_output=True,
            check=True,
        )
        .stdout.decode()
        .splitlines()
    )
    toxenvs = [env for env in os.environ.get("TOXENV", "").split(",") if env]
    for envname in envnames:

        if toxenvs and not any(fnmatch.fnmatch(envname, f"*{e}*") for e in toxenvs):
            continue

        # Run the environment.
        output_dir = results_dir / envname
        output_dir.mkdir(exist_ok=True, parents=True)
        test_output_file = output_dir / f"test_{envname}.xml"
        tox_output_file = output_dir / f"tox_{envname}.json"
        subprocess.run(
            [
                sys.executable,
                "-m",
                "tox",
                "--result-json",
                str(tox_output_file),
                "-e",
                envname,
            ],
            cwd=str(project_tempdir),
            check=False,
            env={
                "TOX_TESTENV_PASSENV": "PYTEST_ADDOPTS",
                "PYTEST_ADDOPTS": f"--tb=long --junitxml={test_output_file}",
                **os.environ,
            },
        )

    return results.AppSuiteRun(
        injected=inject,
        dependent_result=results.DependentResult.from_dir(
            output_dir=results_dir, url=project_url
        ),
    )


def run_many(project_urls: t.List[str], inject: str) -> t.List[results.DependentResult]:
    inject = resolve_inject(inject)
    url_to_res = {}
    for url in project_urls:
        url_to_res[url] = run_one(project_url=url, inject=inject)

    return url_to_res


def extract_failed_tests(
    dependent_result: results.DependentResult
) -> t.Set[results.FailedTest]:
    out = set()
    for suite_run in dependent_result.suite_runs:
        suite = suite_run.suite

        for test in suite.test_cases:
            if test.failure is not None:
                failed = results.FailedTest.from_test_case(test)

                out.add(failed)

    return frozenset(out)


def compare(project_urls: t.List[str], inject_new: str, inject_base: str):
    base_result = run_many(project_urls, inject_base)
    new_result = run_many(project_urls, inject_new)

    db = satests.Database.from_string("sqlite:////tmp/mydb", echo=True)
    db.init()

    for url, result in base_result.items():
        satests.insert_result(db, result)

    for url, result in new_result.items():
        satests.insert_result(db, result)


"""
        SELECT *
        FROM test_case_run tcr
        LEFT JOIN test_failure tf ON tcr.test_failure_id = tf.test_failure_id
        LEFT JOIN test_suite_run tsr ON tsr.test_suite_run_id = tcr.test_suite_run_id
        LEFT JOIN toxenv_run ter ON ter.test_suite_run_id = tsr.test_suite_run_id
        LEFT JOIN tox_run tr ON tr.tox_run_id = ter.tox_run_id

"""
