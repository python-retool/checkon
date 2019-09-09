import pathlib

import click

from . import app


def run_cli(urls_lists, **kw):
    urls = [url for urls in urls_lists for url in urls]

    print(app.run_many(project_urls=urls, **kw))


class ListFromFile(click.File):
    def convert(self, value, param, ctx):
        return [line.strip() for line in super().convert(value, param, ctx).readlines()]


def read_from_file(file):
    return [line.strip() for line in file.readlines()]


dependents = [
    click.Command(
        "dependents-from-pypi",
        params=[
            click.Argument(["pypi-name"]),
            click.Option(
                ["--api-key"], required=True, envvar="CHECKON_LIBRARIESIO_API_KEY"
            ),
            click.Option(
                ["--limit"],
                type=int,
                help="Maximum number of dependents to find.",
                default=5,
            ),
        ],
        callback=app.get_dependents,
        help="Get dependent projects from PyPI, via https://libraries.io API",
    ),
    click.Command(
        "dependents-from-file",
        params=[click.Argument(["file"], type=click.File())],
        help="List dependent project urls in a file, line-separated.",
        callback=read_from_file,
    ),
    click.Command(
        "dependents",
        params=[click.Argument(["dependents"], nargs=-1, required=True)],
        callback=lambda dependents: list(dependents),
        help="List dependent project urls on the command line.",
    ),
]


test = click.Group(
    "test",
    commands={c.name: c for c in dependents},
    params=[click.Option(["--inject"])],
    result_callback=run_cli,
    chain=True,
)


def list_cli(dicts):
    return dicts


list_commands = click.Group(
    "list", commands={c.name: c for c in dependents}, result_callback=list_cli
)
cli = click.Group("run", commands={"test": test, "list": list_commands})
