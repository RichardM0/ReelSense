import requests
import pandas as pd

API_KEY = "c9beeea715999df6bdcef6e7140e35b0"
BASE_URL = "https://api.themoviedb.org/3/movie/popular"

def fetch_movies(pages):
    all_movies = []

    for page in range(1, pages+1):
        url = f"{BASE_URL}?api_key={API_KEY}&language=en-US&page={page}"
        r = requests.get(url).json()

        for movie in r["results"]:
            movie_data = {
                "id": movie["id"],
                "title": movie["title"],
                "overview": movie["overview"],
                "popularity": movie["popularity"],
                "poster": movie.get("poster_path", None),
                "genre_ids": movie["genre_ids"],
                "vote_avg": movie["vote_average"]
            }
            all_movies.append(movie_data)

    df = pd.DataFrame(all_movies)
    df.to_csv("movies.csv", index=False)
    print("Saved movies.csv!")

if __name__ == "__main__":
    fetch_movies(pages=100)
