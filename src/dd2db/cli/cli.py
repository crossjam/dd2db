import bz2
import logging
import os.path
import subprocess
import sys

from importlib import resources
from pathlib import Path
from pprint import pformat

import click
import httpx as requests
import psycopg2

from psycopg2 import sql

from .logconfig import DEFAULT_LOG_FORMAT, logging_config

from .exporter import _exporters, csv_headers

from ..postgresql.dbconfig import connect_db, Config
from ..postgresql.sql import pre_ingest_sql, post_ingest_sql, drop_sql


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


@cli.group(name="discogs")
@click.pass_context
def discogs(ctx):
    """Command set for working with Discogs data dumps"""
    pass


@cli.group(name="postgres")
@click.pass_context
def postgres(ctx):
    """Command set for Postgres work with Discogs data"""
    pass


@cli.group(name="sqlite")
@click.pass_context
def sqlite(ctx):
    """Command set for sqlite3 work with Discogs data"""
    pass


@discogs.command(name="export")
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
    help="Limit export to some entity types (repeatable)",
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


def postgres_load_csv(filename, db):
    logging.info(f"Importing data from {filename}")
    base, fname = os.path.split(filename)
    table, ext = fname.split(".", 1)
    if ext.startswith("csv"):
        q = sql.SQL("COPY {} ({}) FROM STDIN WITH CSV HEADER").format(
            sql.Identifier(table),
            sql.SQL(", ").join(map(sql.Identifier, csv_headers[table])),
        )

    if ext == "csv":
        fp = open(filename)
    elif ext == "csv.bz2":
        fp = bz2.BZ2File(filename)
    else:
        logging.error("%s doesn't have recognized extension", filename)

    cursor = db.cursor()
    cursor.copy_expert(q, fp)
    db.commit()


@postgres.command(name="importcsv")
@click.option(
    "--pgconfig",
    "pgservicefile",
    default=Path("~/.pg_service.conf").expanduser(),
    envvar="PGSERVICEFILE",
    type=click.Path(dir_okay=False, readable=True, resolve_path=True, path_type=Path),
    help="Location of a PostgreSQL configuration file",
)
@click.option(
    "--dry-run/--no-dry-run",
    default=False,
    help="Disable command execution",
    show_default=True,
)
@click.option(
    "--service",
    type=click.STRING,
    default="discogs",
    show_default=True,
    help="Select a service segment from the PostgreSQL configuration file",
)
@click.option(
    "--init-db/--no-init-db",
    default=False,
    help="Initialize PostgreSQL tables, constraints, and indexes",
    show_default=True,
)
@click.argument(
    "fnames",
    nargs=-1,
    type=click.Path(dir_okay=False, readable=True, resolve_path=True, path_type=Path),
)
def pgimportcsv(fnames, pgservicefile, dry_run, service, init_db):
    """Ingest csv files into a PostgreSQL database"""

    if not fnames:
        logging.error("No files passed on command line, exiting")
        sys.exit(0)

    logging.info("Passed pg service file: %s", pgservicefile)
    logging.info("Ingesting %d csv files: %s", len(fnames), fnames)

    root = Path(__file__).resolve()

    if not pgservicefile.exists():
        pgservicefile = root.parent / "postgresql.conf"
        pgservicefile = Path(os.path.join(root, "postgresql.conf"))
        logging.warn("Set pg service configuration to: %s", pgservicefile)

    logging.info("pg servicefile: %s", pgservicefile)
    logging.info("dry_run: %s", dry_run)

    db = psycopg2.connect(**{"service": service})

    if init_db:
        for fname in pre_ingest_sql:
            logging.info("Executing pre-ingest sql file: %s", fname)
            cmd = ["psql", f"service={service}", "--file", str(fname)]
            logging.info("Command: %s", cmd)
            if dry_run:
                continue
            subprocess.run(
                cmd,
                check=True,
                # shell=True,
                stdout=sys.stdout,
                stderr=sys.stderr,
            )

    for fname in fnames:
        logging.info("Loading %s", fname)
        if dry_run:
            continue
        postgres_load_csv(fname, db)

    if init_db:
        for fname in post_ingest_sql:
            logging.info("Executing post-ingest sql file: %s", fname)
            cmd = ["psql", f"service={service}", "--file", str(fname)]
            logging.info("Command: %s", cmd)
            if dry_run:
                continue
            subprocess.run(
                cmd,
                check=True,
                # shell=True,
                stdout=sys.stdout,
                stderr=sys.stderr,
            )


@postgres.command(name="drop")
@click.option(
    "--pgconfig",
    "pgservicefile",
    default=Path("~/.pg_service.conf").expanduser(),
    envvar="PGSERVICEFILE",
    type=click.Path(dir_okay=False, readable=True, resolve_path=True, path_type=Path),
    help="Location of a PostgreSQL configuration file",
)
@click.option(
    "--dry-run/--no-dry-run",
    default=False,
    help="Disable command execution",
    show_default=True,
)
@click.option(
    "--service",
    type=click.STRING,
    default="discogs",
    show_default=True,
    help="Select a service segment from the PostgreSQL configuration file",
)
def pgdrop(pgservicefile, dry_run, service):
    """Drop discogs data PostgreSQL tables, constraints, and indexes"""

    logging.info("Passed pg service file: %s", pgservicefile)

    root = Path(__file__).resolve()

    if not pgservicefile.exists():
        pgservicefile = root.parent / "postgresql.conf"
        pgservicefile = Path(os.path.join(root, "postgresql.conf"))
        logging.warn("Set pg service configuration to: %s", pgservicefile)

    logging.info("pg servicefile: %s", pgservicefile)
    logging.info("dry_run: %s", dry_run)

    db = psycopg2.connect(**{"service": service})
    for fname in drop_sql:
        logging.info("Executing drop sql file: %s", fname)
        cmd = ["psql", f"service={service}", "--file", str(fname)]
        logging.info("Command: %s", cmd)
        if dry_run:
            continue
        subprocess.run(
            cmd,
            check=True,
            # shell=True,
            stdout=sys.stdout,
            stderr=sys.stderr,
        )


@postgres.command(name="init")
@click.option(
    "--pgconfig",
    "pgservicefile",
    default=Path("~/.pg_service.conf").expanduser(),
    envvar="PGSERVICEFILE",
    type=click.Path(dir_okay=False, readable=True, resolve_path=True, path_type=Path),
    help="Location of a PostgreSQL configuration file",
)
@click.option(
    "--dry-run/--no-dry-run",
    default=False,
    help="Disable command execution",
    show_default=True,
)
@click.option(
    "--service",
    type=click.STRING,
    default="discogs",
    show_default=True,
    help="Select a service segment from the PostgreSQL configuration file",
)
def pginit(pgservicefile, dry_run, service):
    """Initializes discogs data PostgreSQL tables"""

    logging.info("Passed pg service file: %s", pgservicefile)

    root = Path(__file__).resolve()

    if not pgservicefile.exists():
        pgservicefile = root.parent / "postgresql.conf"
        pgservicefile = Path(os.path.join(root, "postgresql.conf"))
        logging.warn("Set pg service configuration to: %s", pgservicefile)

    logging.info("pg servicefile: %s", pgservicefile)
    logging.info("dry_run: %s", dry_run)

    db = psycopg2.connect(**{"service": service})
    for fname in pre_ingest_sql:
        logging.info("Executing pre-ingest sql file: %s", fname)
        cmd = ["psql", f"service={service}", "--file", str(fname)]
        logging.info("Command: %s", cmd)
        if dry_run:
            continue
        subprocess.run(
            cmd,
            check=True,
            # shell=True,
            stdout=sys.stdout,
            stderr=sys.stderr,
        )


@postgres.command(name="optimize")
@click.option(
    "--pgconfig",
    "pgservicefile",
    default=Path("~/.pg_service.conf").expanduser(),
    envvar="PGSERVICEFILE",
    type=click.Path(dir_okay=False, readable=True, resolve_path=True, path_type=Path),
    help="Location of a PostgreSQL configuration file",
)
@click.option(
    "--dry-run/--no-dry-run",
    default=False,
    help="Disable command execution",
    show_default=True,
)
@click.option(
    "--service",
    type=click.STRING,
    default="discogs",
    show_default=True,
    help="Select a service segment from the PostgreSQL configuration file",
)
def pgoptimize(pgservicefile, dry_run, service):
    """Initializes discogs data PostgreSQL constraints and indexes"""

    logging.info("Passed pg service file: %s", pgservicefile)

    root = Path(__file__).resolve()

    if not pgservicefile.exists():
        pgservicefile = root.parent / "postgresql.conf"
        pgservicefile = Path(os.path.join(root, "postgresql.conf"))
        logging.warn("Set pg service configuration to: %s", pgservicefile)

    logging.info("pg servicefile: %s", pgservicefile)
    logging.info("dry_run: %s", dry_run)

    db = psycopg2.connect(**{"service": service})

    for fname in post_ingest_sql:
        logging.info("Executing post-ingest sql file: %s", fname)
        cmd = ["psql", f"service={service}", "--file", str(fname)]
        logging.info("Command: %s", cmd)
        if dry_run:
            continue
        subprocess.run(
            cmd,
            check=True,
            # shell=True,
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
