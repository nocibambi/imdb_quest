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

`imdb_quest.py` contains the mains script including the three functions.

### From shell

```shell
python -m imdb_quest
```

### From IDE

`imdb_quest.py` uses the [Jupytext percentage format](https://jupytext.readthedocs.io/en/latest/formats.html#the-percent-format). This allows you to run the script interactively in IDEs like VSCode.

## Tests

```shell
pytest test_imdb_quest.py
```
