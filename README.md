# dd2db: Discogs datasets 2 database

A recasting of code from the
[discogs-xml2db](https://github.com/philipmat/discogs-xml2db)
repository to advance into the modern era of Python.

A CLI toolkit oriented around taking the [Discogs Data dumps][1] and
ingesting them into various database systems,
[sqlite3](https://www.sqlite.org) and
[Postgresql](https://www.postgresql.org) to start with.  The data is
real world recorded music data (supports
[discogs.com](https://discogs.com), quite longitudinal (spanning 16
years as of 2024), updated monthly, and of course a bit messy.

[1]: https://data.discogs.com/
