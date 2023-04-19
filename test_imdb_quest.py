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


