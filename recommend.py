import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# mapping genre ids to genre names
genres = {
    28: "Action",
    12: "Adventure",   
    16: "Animation",
    35: "Comedy",
    80: "Crime",
    99: "Documentary",
    18: "Drama",
    10751: "Family",
    14: "Fantasy",
    36: "History",
    27: "Horror",
    10402: "Music",
    9648: "Mystery",
    10749: "Romance",
    878: "Science Fiction",
    10770: "TV Movie",
    53: "Thriller",
    10752: "War",
    37: "Western"
}

# classifying moods for easy user experience
moods = {
    "Happy": ["Comedy", "Family", "Animation", "Music", "Romance"],
    "Sad": ["Drama", "Documentary", "History"],
    "Energized": ["Action", "Adventure", "Science Fiction", "Fantasy"],
    "Scared": ["Horror", "Thriller", "Mystery", "Crime"],
    "Calm": ["Romance", "Drama", "Documentary"],
    "Romantic": ["Romance", "Drama", "Music"],
    "Adventurous": ["Action", "Adventure", "Fantasy", "Science Fiction"],
    "Humorous": ["Comedy", "Animation", "Family"],
    "Suspenseful": ["Thriller", "Mystery", "Crime", "Horror"],
    "Curious": ["Documentary", "History", "Science Fiction"],
}

# read in movies data from csv
movies_df = pd.read_csv("movies.csv")
# create a score column to rank movies by mood later on
movies_df["score"] = movies_df["popularity"] * 0.4 + movies_df["vote_avg"] * 0.6

# initialize TF-IDF Vectorizer and compute similarity matrix
vectorizer = TfidfVectorizer(stop_words='english')
plots = vectorizer.fit_transform(movies_df["overview"].fillna(""))
similarity_matrix = cosine_similarity(plots)

# function to get the top n most similar movies to a specific id 
def get_similar_movies(movie_id, top_n):
    # find index of the movie in the DF
    idx = movies_df.index[movies_df["id"] == movie_id][0]
    
    # create set of genre ids for the input movie
    input_genres = set(eval(movies_df["genre_ids"].iloc[idx]))
    
    # get similarity scores
    sim_scores = similarity_matrix[idx]

    # sort indices by similarity
    similar_indices = np.argsort(sim_scores)[::-1][1:]  # Skip self

    # storing top n unique movie ids and their induces
    ids = []
    top_n_indices = []

    # loop until we have top_n unique movies
    while len(ids) < top_n:
        # loop through all similar indices
        for i in similar_indices:
            # create set of genre ids for candidate movie
            candidate_genres = set(eval(movies_df["genre_ids"].iloc[i]))
            # check if the candidate and the input movie share at least one genre
            hasShared = bool(candidate_genres & input_genres)
            # if the id has not been seen, add it
            if movies_df["id"].iloc[i] not in ids and hasShared:
                ids.append(movies_df["id"].iloc[i])
                top_n_indices.append(i)
            # break if we have enough movies
            if len(ids) >= top_n:
                break

    return movies_df.iloc[top_n_indices][["id", "title", "overview", "genre_ids", "vote_avg", "poster", "popularity"]]

# function to get similar movies for a list of movie ids
def get_all_similar_movies(movie_ids, top_n):
    # inputs a list of ids to get similar movies for each
    all_movies = {}
    # loops through all ids and gets similar movies
    for movie_id in movie_ids:
        similar = get_similar_movies(movie_id, top_n)
        movies = set(similar["title"].tolist())
        all_movies[movies_df[movies_df["id"] == movie_id]["title"].iloc[0]] = movies
    return all_movies

test_case = get_all_similar_movies(movies_df["id"].iloc[0:3], 5)


