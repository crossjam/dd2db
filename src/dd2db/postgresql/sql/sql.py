from pathlib import Path

pre_ingest_sql = [
    Path(__file__).parent / "CreateTables.sql",
]

post_ingest_sql = [
    Path(__file__).parent / "CreatePrimaryKeys.sql",
    Path(__file__).parent / "CreateFKConstraints.sql",
    Path(__file__).parent / "CreateIndexes.sql",
]

drop_sql = [
    Path(__file__).parent / "DropIndexes.sql",
    Path(__file__).parent / "DropFKConstraints.sql",
    Path(__file__).parent / "DropPrimaryKeys.sql",
    Path(__file__).parent / "DropTables.sql",
]
