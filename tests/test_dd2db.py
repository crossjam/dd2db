from click.testing import CliRunner
from dd2db.cli import cli


def test_version():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert result.output.startswith("cli, version ")


def test_subcommands_exist():
    subgroups = ["postgres", "sqlite", "discogs"]
    db_subcommands = ["init", "optimize", "drop", "importcsv"]

    runner = CliRunner()
    with runner.isolated_filesystem():
        for subgroup in subgroups:
            result = runner.invoke(cli, [subgroup, "--help"])
            assert result.exit_code == 0

        for subgroup in ["postgres", "sqlite"]:
            for subcommand in db_subcommands:
                result = runner.invoke(cli, [subgroup, subcommand, "--help"])
                assert result.exit_code == 0
