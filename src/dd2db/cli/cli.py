import logging
import sys

from importlib import resources
from pathlib import Path

import click
import httpx as requests

from .logconfig import DEFAULT_LOG_FORMAT, logging_config

from .exporter import _exporters


@click.group()
@click.version_option()
@click.option(
    "--log-format",
    type=click.STRING,
    default=DEFAULT_LOG_FORMAT,
    help="Python logging format string",
)
@click.option(
    "--log-level", default="ERROR", help="Python logging level", show_default=True
)
@click.option(
    "--log-file",
    help="Python log output file",
    type=click.Path(dir_okay=False, writable=True, resolve_path=True),
    default=None,
)
@click.pass_context
def cli(ctx, log_format, log_level, log_file):
    """dd2db: Discogs data 2 database CLI utilities"""

    logging_config(log_format, log_level, log_file)

    ctx.ensure_object(dict)


@cli.command(name="export")
@click.option(
    "--bz2 / --no-bz2",
    default=False,
    help="Compress output files using bz2 compression",
)
@click.option(
    "--limit",
    default=None,
    type=click.INT,
    help="Limit export to some number of entities",
)
@click.option(
    "--export",
    multiple=True,
    type=click.Choice(
        ["artist", "label", "release", "master", "all"],
        case_sensitive=False,
    ),
    help="Limit export to some entities (repeatable)",
)
@click.option(
    "--apicounts/--no-apicounts",
    default=False,
    help="Check entities counts with Discogs API",
)
@click.option("--dry-run/--no-dry-run", default=False, help="Do not write")
@click.option("--debug/--no-debug", default=False, help="Enable debugging output")
@click.argument(
    "datadir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
)
@click.argument(
    "output",
    type=click.Path(
        exists=True,
        file_okay=False,
        dir_okay=True,
        path_type=Path,
    ),
    default=Path.cwd(),
)
@click.pass_context
def export_dumps(ctx, datadir, output, bz2, limit, export, apicounts, dry_run, debug):
    """Convert Discogs data dump XML into CSV for future ingestion into a database

    DATADIR holds the data dump files, OUTPUT is where the result CSV
    export files will be written

    """

    logging.info("DATADIR: %s", datadir)
    logging.info("OUTDIR: %s", output)
    logging.info("bz2: %s", bz2)
    logging.info("limit: %s", limit)
    logging.info("apicounts: %s", apicounts)
    logging.info("dry_run: %s", dry_run)

    if not set(export):
        logging.error("Need to specify at least one export type, exiting")
        sys.exit(1)

    if "all" in export:
        export = set(["artist", "label", "release", "master"])

    logging.info("export: %s", set(export))

    # this is used to get a rough idea of how many items we can expect
    # in each dump file so that we can show the progress bar
    rough_counts = {
        "artists": 5000000,
        "labels": 1100000,
        "masters": 1250000,
        "releases": 8500000,
    }
    if apicounts:
        try:
            r = requests.get("https://api.discogs.com/", timeout=5)
            rough_counts.update(r.json().get("statistics"))
            logging.info("Succeeded in getting count statistics via API call")
        except:
            pass

    logging.info("Entity counts: %s", rough_counts)

    for entity in export:
        expected_count = rough_counts[f"{entity}s"]
        exporter = _exporters[entity](
            datadir,
            output,
            limit=limit,
            bz2=bz2,
            debug=debug,
            max_hint=min(expected_count, limit or expected_count),
            dry_run=dry_run,
        )
        logging.info("%s: %s", entity, exporter)
        exporter.export()
