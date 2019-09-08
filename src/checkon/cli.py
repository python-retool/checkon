import pathlib

import click

from . import app


def run_cli(inject, project_url, project_urls_file):
    if project_urls_file:
        project_urls = (
            list(project_url) + pathlib.Path(project_urls_file).read_text().splitlines()
        )
    app.run_many(inject=inject, project_urls=project_urls)


cli = click.Command(
    "run",
    params=[
        click.Argument(["inject"], type=lambda x: pathlib.Path(x).resolve()),
        click.Argument(["project_url"], nargs=-1, required=False),
        click.Option(["--project-urls-file"], type=click.File()),
    ],
    callback=run_cli,
)
