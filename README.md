# zmovies
Show the movies I watch

## Running

```sh
uv sync
uv run flask --app zmovies run
```

Data is read from the `Datadir` directory (override with the `ZMOVIES_DATADIR`
environment variable) and loaded into `instance/zmovies.db` on startup.
