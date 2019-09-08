import pathlib

import click

from . import app


cli = click.Command(
    "run",
    params=[
        click.Argument(["inject"], type=lambda x: pathlib.Path(x).resolve()),
        click.Argument(["project_url"]),
    ],
    callback=app.run,
)
