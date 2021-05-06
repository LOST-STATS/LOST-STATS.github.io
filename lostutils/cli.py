from typing import List

import click
from tqdm.cli import tqdm

from .constants import R_DOCKER_IMAGE
from .fix_links import fix_md
from .pathutils import expand_and_filter_filenames
from .style import format_file


@click.group()
def cli():
    """Utilities for testing and cleaning LOST"""
    pass


@cli.command("style")
@click.argument("filename", nargs=-1, type=click.Path())
@click.option(
    "--skip",
    multiple=True,
    type=click.Path(),
    help="Files to skip. Follows same expansion rules as FILENAME",
)
@click.option(
    "--docker-r",
    type=str,
    default=R_DOCKER_IMAGE,
    help="Tag of the docker image in which to run styler for R code",
)
def style_command(filename: List[str], skip: List[str], docker_r: str):
    """
    Attempt to style the code samples using black and styler.
    You must specify at least one FILENAME. Note that filenames are
    treated as glob patterns relative to the working directory. After
    any glob returns, we will filter for filenames that end in `.md`.
    """
    filenames = expand_and_filter_filenames(filename, skip)
    for filename in tqdm(filenames):
        fixed_md = format_file(filename, r_docker_image=docker_r)
        with open(filename, "wt") as outfile:
            print(fixed_md, file=outfile)


@cli.command("links")
@click.argument("filename", nargs=-1, type=click.Path())
@click.option(
    "--skip",
    multiple=True,
    type=click.Path(),
    help="Files to skip. Follows same expansion rules as FILENAME",
)
def links_command(filename: List[str], skip: List[str]):
    """
    Attempt to fix links in accordance with a predefined list of rules.
    You must specify at least one FILENAME. Note that filenames are
    treated as glob patterns relative to the working directory. After
    any glob returns, we will filter for filenames that end in `.md`.
    """
    filenames = expand_and_filter_filenames(filename, skip)
    for filename in tqdm(filenames):
        fixed_md = fix_md(filename)
        with open(filename, "wt") as outfile:
            outfile.write(fixed_md)


if __name__ == "__main__":
    cli()
