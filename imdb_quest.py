# %%
import pandas as pd
from requests import request
from bs4 import BeautifulSoup
import os
import numpy as np
import pandera as pa
from dotenv import load_dotenv

# %%
load_dotenv()
MovieSchema: pd.DataFrame = pa.DataFrameSchema(
    {
        "rating": pa.Column(float, checks=pa.Check.le(10)),
        "number of ratings": pa.Column(int, checks=pa.Check.between(100e3, 3e6)),
        "number of oscars": pa.Column(int, checks=pa.Check.le(11)),
        "title": pa.Column(str),
    }
)


def scraper(
    top_number: int = 20,
) -> pd.DataFrame:
    imdb_top_url = "https://www.imdb.com/chart/top/"
    headers = {"Accept-Language": "en-US,en;q=0.5"}

    source = request("GET", imdb_top_url, headers=headers)
    soup = BeautifulSoup(source.text, features="html.parser")
    table = soup.find("table", attrs={"class": "chart full-width"})
    table_body = table.find("tbody")

    movies_list: list[dict] = []
    rows = table_body.find_all("tr")
    for row in rows:
        title_column = row.find_all("td", attrs={"class": "titleColumn"})[0]
        title: str = title_column.find("a").text
        imdb_id: str = title_column.find("a").attrs["href"].split("/")[-2]

        try:
            awards_url: str = f"https://www.imdb.com/title/{imdb_id}/awards/"
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


def review_penalizer(movies_df: pd.DataFrame) -> pd.Series:
    max_number_of_ratings: int = movies_df["number of ratings"].max()
    review_penalties: pd.Series = (
        (max_number_of_ratings - movies_df["number of ratings"]) // 100e3
    ) * 0.1

    return review_penalties


# %%


def oscar_calculator(top_movies: pd.DataFrame) -> pd.Series:
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
    movies_path: str = os.environ["MOVIES_PATH"]

    top_movies: pd.DataFrame = scraper(top_number=20)
    review_penalties: pd.Series = review_penalizer(top_movies)
    oscar_points: pd.Series = oscar_calculator(top_movies)
    top_movies["adjusted rating"] = (
        top_movies["rating"] - review_penalties + oscar_points
    )

    MovieSchemaAdjusted = MovieSchema.add_columns(
        {"adjusted rating": pa.Column(float, checks=pa.Check.le(11.5))}
    )
    MovieSchemaAdjusted.validate(top_movies)

    top_movies.sort_values("adjusted rating", ascending=False).to_json(movies_path)
# %%
