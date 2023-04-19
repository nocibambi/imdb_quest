# DataPao IMDB Challenge

Author: András Novoszáth

## Environment setup

Requires poetry >=v1.1.12 ([installation](https://python-poetry.org/docs/#installation))

```shell
poetry shell
poetry install
```

## Parameters

You can define some parameters in `.env`:

- `MOVIES_PATH`: the path and filename of the results
- `TOP_NUMBER`: the number of top movies to collect information about

## Running the script

```shell
python -m imdb_quest
```

## Tests

```shell
pytest
```
