import streamlit as st
import pandas as pd
import numpy as np
from recommend import get_similar_movies, get_all_similar_movies, movies_df
from PIL import Image
import requests
from io import BytesIO

# Set page config
st.set_page_config(page_title="ReelSense", layout="wide", initial_sidebar_state="expanded")

# Initialize session state for liked movies and navigation
if "liked_movies" not in st.session_state:
    st.session_state.liked_movies = []

if "page" not in st.session_state:
    st.session_state.page = "home"

if "selected_movie_id" not in st.session_state:
    st.session_state.selected_movie_id = None

# Function to load poster image from URL
@st.cache_data
def load_poster(poster_path):
    if pd.isna(poster_path) or poster_path == "":
        return None
    try:
        url = f"https://image.tmdb.org/t/p/w342{poster_path}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return Image.open(BytesIO(response.content))
    except:
        pass
    return None

# Function to display movie grid
def display_movie_grid(movies, cols=5, clickable=True, key_prefix=""):
    if len(movies) == 0:
        st.write("No movies to display.")
        return None
    
    rows = (len(movies) + cols - 1) // cols
    movie_index = 0
    
    for row in range(rows):
        cols_list = st.columns(cols)
        for col_idx in range(cols):
            movie_idx = row * cols + col_idx
            if movie_idx >= len(movies):
                break
            
            with cols_list[col_idx]:
                movie = movies.iloc[movie_idx]
                poster = load_poster(movie["poster"])
                
                if poster:
                    st.image(poster, use_container_width=True)
                else:
                    st.write("No Poster Available")
                
                st.write(f"**{movie['title'][:20]}...**" if len(movie['title']) > 20 else f"**{movie['title']}**")
                
                if clickable:
                    if st.button("View Details", key=f"{key_prefix}view_{movie['id']}_{movie_index}", use_container_width=True):
                        st.session_state.selected_movie_id = movie['id']
                        st.session_state.page = "movie_detail"
                        st.rerun()
                
                movie_index += 1

# Function to display movie detail page
def display_movie_detail(movie_id):
    movie = movies_df[movies_df["id"] == movie_id]
    
    if movie.empty:
        st.error("Movie not found!")
        return
    
    movie = movie.iloc[0]
    
    # Back button
    if st.button("← Back to Home", key=f"back_{movie_id}", use_container_width=True):
        st.session_state.page = "home"
        st.session_state.selected_movie_id = None
        st.rerun()
    
    # Movie details layout
    col1, col2 = st.columns([1, 2])
    
    with col1:
        poster = load_poster(movie["poster"])
        if poster:
            st.image(poster, use_container_width=True)
        else:
            st.write("No Poster Available")
        
        # Like button
        if movie_id in st.session_state.liked_movies:
            if st.button("❤️ Unlike", key=f"unlike_{movie_id}", use_container_width=True):
                st.session_state.liked_movies.remove(movie_id)
                st.success("Removed from liked movies!")
                st.rerun()
        else:
            if st.button("🤍 Like", key=f"like_{movie_id}", use_container_width=True):
                st.session_state.liked_movies.append(movie_id)
                st.success("Added to liked movies!")
                st.rerun()
    
    with col2:
        st.title(movie["title"])
        st.write(f"**Rating:** {10*movie['vote_avg']:.2f}/10")
        st.write(f"**Popularity:** {100*movie['popularity']:.2f}")
        
        st.subheader("Overview")
        st.write(movie["overview"])
    
    # Similar movies section
    st.subheader("Similar Movies")
    similar_movies = get_similar_movies(movie_id, 6)
    display_movie_grid(similar_movies, cols=3, clickable=True, key_prefix=f"detail_{movie_id}_")

# Function to display liked movies and their recommendations
def display_liked_movies():
    st.title("Your Liked Movies")
    
    if not st.session_state.liked_movies:
        st.write("You haven't liked any movies yet!")
        if st.button("← Back to Home", key="back_no_liked", use_container_width=True):
            st.session_state.page = "home"
            st.rerun()
        return
    
    # Back button
    if st.button("← Back to Home", key="back_liked", use_container_width=True):
        st.session_state.page = "home"
        st.rerun()
    
    st.write(f"You have liked {len(st.session_state.liked_movies)} movie(s)")
    
    # Display liked movies
    st.subheader("Your Liked Movies")
    liked_movies_df = movies_df[movies_df["id"].isin(st.session_state.liked_movies)]
    display_movie_grid(liked_movies_df, cols=5, clickable=True, key_prefix="liked_")
    
    # Find similar movies button
    st.subheader("Find Similar Movies")
    if st.button("Get Similar Movies for All Liked Movies", key="similar_btn", use_container_width=True):
        st.session_state.page = "similar_recommendations"
        st.rerun()

# Function to display similar recommendations
def display_similar_recommendations():
    st.title("Similar Movies for Your Liked Movies")
    
    if st.button("← Back to Liked Movies", key="back_similar", use_container_width=True):
        st.session_state.page = "liked"
        st.rerun()
    
    similar_dict = get_all_similar_movies(st.session_state.liked_movies, 3)
    
    if not similar_dict:
        st.write("No similar movies found.")
        return
    
    for idx, (movie_title, similar_titles) in enumerate(similar_dict.items()):
        st.subheader(f"Similar to: {movie_title}")
        
        similar_movies_df = movies_df[movies_df["title"].isin(similar_titles)]
        display_movie_grid(similar_movies_df, cols=3, clickable=True, key_prefix=f"similar_{idx}_")
        st.write("---")

# Function to search movies
def display_search():
    st.title("Search Movies")
    
    if st.button("← Back to Home", key="back_search", use_container_width=True):
        st.session_state.page = "home"
        st.rerun()
    
    search_query = st.text_input("Search for a movie...", placeholder="Enter movie title", key="search_input")
    
    if search_query:
        results = movies_df[movies_df["title"].str.contains(search_query, case=False, na=False)]
        
        if len(results) > 0:
            st.write(f"Found {len(results)} movie(s)")
            display_movie_grid(results, cols=5, clickable=True, key_prefix="search_")
        else:
            st.write("No movies found matching your search.")

# Function to display home page
def display_home():
    st.title("🎬 ReelSense - Movie Recommendations")
    st.write("Discover your next favorite movie!")
    
    # Get top 25 movies sorted by popularity
    top_movies = movies_df.nlargest(25, "popularity")
    
    st.subheader("Top 25 Popular Movies")
    display_movie_grid(top_movies, cols=5, clickable=True, key_prefix="home_")

with st.sidebar:
    st.title("Navigation")
    
    # Create navigation buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🏠 Home", use_container_width=True, key="nav_home"):
            st.session_state.page = "home"
    
    with col2:
        if st.button("❤️ Liked", use_container_width=True, key="nav_liked"):
            st.session_state.page = "liked"
    
    with col3:
        if st.button("🔍 Search", use_container_width=True, key="nav_search"):
            st.session_state.page = "search"
    
    st.divider()
    st.write(f"📌 Liked Movies: {len(st.session_state.liked_movies)}")
    
    if st.session_state.liked_movies:
        st.write("**Your Liked Movies:**")
        for movie_id in st.session_state.liked_movies:
            movie = movies_df[movies_df["id"] == movie_id]
            if not movie.empty:
                title = movie.iloc[0]["title"]
                st.write(f"• {title}")

# Main page routing
if st.session_state.page == "home":
    display_home()
elif st.session_state.page == "movie_detail":
    if st.session_state.selected_movie_id:
        display_movie_detail(st.session_state.selected_movie_id)
    else:
        st.session_state.page = "home"
elif st.session_state.page == "liked":
    display_liked_movies()
elif st.session_state.page == "similar_recommendations":
    display_similar_recommendations()
elif st.session_state.page == "search":
    display_search()
else:
    st.session_state.page = "home"
