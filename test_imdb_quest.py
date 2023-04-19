import pandas as pd
import pytest

from imdb_quest import scraper, review_penalizer, oscar_calculator


@pytest.fixture
def top_movies() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "rating": [9.6, 9.4, 7.4],
            "number of ratings": [2456123, 1258369, 456123],
            "number of oscars": [0, 2, 4],
            "title": [
                "Movie 1",
                "Movie 2",
                "Movie 3",
            ],
        }
    )


def test_scraper():
    # The `scraper` function validates the data in running time.
    # Breaking up the function would allow more granular testing. TBD.
    movies = scraper(top_number=3)
    assert not movies.isna().any().any()


def test_review_penalizer(top_movies):
    assert all(
        adjust_by_number_of_rankings(top_movies).values
        == pd.Series([-0, -1.1, -2]).values
    )


def test_oscar_calculator(top_movies):
    assert all(
        adjust_by_number_of_oscars(top_movies).values == pd.Series([0, 0.3, 0.5]).values
    )
