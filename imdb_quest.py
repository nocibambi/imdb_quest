# %%
from dotenv import load_dotenv
import os

import pandas as pd
from requests import request
from bs4 import BeautifulSoup
import numpy as np
import pandera as pa


# %%
MovieSchema: pd.DataFrame = pa.DataFrameSchema(
    {
        "rating": pa.Column(float, checks=pa.Check.le(10), nullable=False),
        "number of ratings": pa.Column(
            int, checks=pa.Check.between(100e3, 3e6), nullable=False
        ),
        "number of oscars": pa.Column(int, checks=pa.Check.le(11)),
        "title": pa.Column(str, unique=True, checks=pa.Check.ne("")),
    },
    strict=True,
)


def scraper(
    top_number: int = 20,
) -> pd.DataFrame:
    """Scrape top movies from IMDB.

    Dimensions to collect:
    - title
    - rating
    - number of ratings
    - number of oscars

    Parameters
    ----------
    top_number : int, optional
        Determines the number of top movies to scrape, by default 20

    Returns
    -------
    pd.DataFrame
        The collected information of the top imdb movies.
    """
    imdb_top_url = "https://www.imdb.com/chart/top/"
    headers = {"Accept-Language": "en-US,en;q=0.5"}

    source = request("GET", imdb_top_url, headers=headers)
    soup = BeautifulSoup(source.text, features="html.parser")
    table_body = soup.find("table", attrs={"class": "chart full-width"}).find("tbody")

    movies_list: list[dict] = []
    rows = table_body.find_all("tr")
    for row in rows:
        title_column = row.find_all("td", attrs={"class": "titleColumn"})[0]
        title: str = title_column.find("a").text
        imdb_id: str = title_column.find("a").attrs["href"].split("/")[-2]

        try:
            awards_url = f"https://www.imdb.com/title/{imdb_id}/awards/"
            awards: list[pd.DataFrame] = pd.read_html(awards_url)
            number_of_oscars: int = sum(
                [(award.loc[:, 0] == "Winner  Oscar").sum() for award in awards]
            )
        except ValueError:
            number_of_oscars = 0

        poster_column = row.find_all("td", attrs={"class": "posterColumn"})[0]
        rank = int(poster_column.find("span", attrs={"name": "rk"}).attrs["data-value"])
        rating = float(
            poster_column.find("span", attrs={"name": "ir"}).attrs["data-value"]
        )
        number_of_ratings = int(
            poster_column.find("span", attrs={"name": "nv"}).attrs["data-value"]
        )

        print(title, rating, number_of_ratings, number_of_oscars)

        movies_list.append(
            {
                "rating": rating,
                "number of ratings": number_of_ratings,
                "number of oscars": number_of_oscars,
                "title": title,
            }
        )

        if rank >= top_number:
            break

    return MovieSchema.validate(pd.DataFrame(movies_list))


# %%


def adjust_by_number_of_rankings(movies_df: pd.DataFrame) -> pd.Series:
    """Adjust rating based on number of ratings.

    Parameters
    ----------
    movies_df : pd.DataFrame
        Movie information. Has to have a "number of ratings" column.

    Returns
    -------
    pd.Series
        Rating adjustments calculated based on the number of ratings.
    """
    max_number_of_ratings: int = movies_df["number of ratings"].max()
    return -((max_number_of_ratings - movies_df["number of ratings"]) // 100e3) * 0.1


# %%


def adjust_by_number_of_oscars(top_movies: pd.DataFrame) -> pd.Series:
    """Adjust rating based on number of oscars.

    Parameters
    ----------
    top_movies : pd.DataFrame
        Movie information. Has to have a "number of oscars" column.

    Returns
    -------
    pd.Series
        Rating adjustments based on number of oscars.
    """
    points_by_oscars: dict[tuple, float] = {
        (0, 1): 0,
        (1, 3): 0.3,
        (3, 6): 0.5,
        (6, 11): 1,
        (11, np.inf): 1.5,
    }

    return (
        pd.cut(
            top_movies["number of oscars"], bins=[0, 1, 3, 6, 11, np.inf], right=False
        )
        .map(
            {
                pd.Interval(interval[0], interval[1], closed="left"): point
                for interval, point in points_by_oscars.items()
            }
        )
        .astype(float)
    )


# %%
if __name__ == "__main__":
    load_dotenv()
    movies_path: str = os.environ["MOVIES_PATH"]
    top_number = int(os.environ["TOP_NUMBER"])

    movies: pd.DataFrame = scraper(top_number=top_number)
    adjustment_by_number_of_rankings: pd.Series = adjust_by_number_of_rankings(movies)
    adjustment_by_number_of_oscars: pd.Series = adjust_by_number_of_oscars(movies)
    movies["adjusted rating"] = (
        movies["rating"]
        + adjustment_by_number_of_rankings
        + adjustment_by_number_of_oscars
    )
    movies = movies.sort_values("adjusted rating", ascending=False)

    MovieSchemaAdjusted = MovieSchema.add_columns(
        {"adjusted rating": pa.Column(float, checks=pa.Check.le(11.5))}
    )
    MovieSchemaAdjusted.validate(movies)

    movies.to_json(movies_path)
# %%
