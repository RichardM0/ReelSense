import streamlit as st
import pandas as pd
from recommend import get_similar_movies


@st.cache_data
def load_data():
	df = pd.read_csv("movies.csv")
	df["title"] = df["title"].fillna("")
	df["overview"] = df["overview"].fillna("")
	return df


movies_df = load_data()

# Styling: tighten inline buttons and poster appearance; fixed heights for consistent grid
st.markdown(
	"""
	<style>
	div.stButton > button { margin: 4px 4px 4px 0px; padding: 6px 8px; }
	.movie-poster-link img { border-radius: 6px; display:block; }
	.movie-title { height: 3.2rem; overflow: hidden; text-overflow: ellipsis; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }
	.movie-poster { width:100%; height:260px; overflow:hidden; }
	.movie-poster img { width:100%; height:100%; object-fit:cover; }
	</style>
	""",
	unsafe_allow_html=True,
)


# Session state defaults
if "page" not in st.session_state:
	st.session_state.page = "home"
if "current_movie" not in st.session_state:
	st.session_state.current_movie = None
if "liked" not in st.session_state:
	st.session_state.liked = set()


# Query param helpers: prefer stable API, fall back to experimental for older Streamlit
def set_qs(**kwargs):
	if hasattr(st, "set_query_params"):
		st.set_query_params(**kwargs)
	elif hasattr(st, "experimental_set_query_params"):
		st.experimental_set_query_params(**kwargs)


def get_qs():
	if hasattr(st, "get_query_params"):
		return st.get_query_params()
	if hasattr(st, "experimental_get_query_params"):
		return st.experimental_get_query_params()
	return {}


def go_to(page, movie_id=None):
	st.session_state.page = page
	st.session_state.current_movie = movie_id
	# keep URL in sync so direct clicks/links work
	if movie_id is None:
		set_qs(page=page)
	else:
		set_qs(page=page, movie_id=movie_id)


# Initialize from URL query params (if present)
params = get_qs()
if "page" in params:
	st.session_state.page = params.get("page", [st.session_state.page])[0]
if "movie_id" in params:
	mv = params.get("movie_id", [None])[0]
	try:
		st.session_state.current_movie = int(mv) if mv is not None else None
	except (TypeError, ValueError):
		st.session_state.current_movie = None


def display_movie_card(movie_row, container, button_prefix=""):
	"""Render a single movie card inside the provided container (column)."""
	movie_id = int(movie_row["id"])
	title = movie_row.get("title", "")
	poster = movie_row.get("poster", None)

	# attempt to fallback to master movies_df if poster missing in provided row
	if not poster or not pd.notna(poster):
		fallback = movies_df[movies_df["id"] == movie_id]
		if not fallback.empty and "poster" in fallback.columns:
			poster = fallback.iloc[0]["poster"]

	with container:
		# poster container with fixed height for consistent grid
		if poster and pd.notna(poster):
			poster_url = "https://image.tmdb.org/t/p/w300" + str(poster)
			st.markdown(
				f'<a class="movie-poster-link movie-poster" href="?page=movie&movie_id={movie_id}"><img src="{poster_url}"/></a>',
				unsafe_allow_html=True,
			)
		else:
			# empty fixed-height placeholder
			st.markdown('<div class="movie-poster" style="background:#eee;"></div>', unsafe_allow_html=True)

		# title with fixed height / ellipsis
		st.markdown(f'<div class="movie-title">**{title}**</div>', unsafe_allow_html=True)

		c1, c2 = st.columns([1, 1])
		with c1:
			if movie_id not in st.session_state.liked:
				if st.button("❤️", key=f"{button_prefix}_like_{movie_id}"):
					st.session_state.liked.add(movie_id)
			else:
				if st.button("💔", key=f"{button_prefix}_unlike_{movie_id}"):
					st.session_state.liked.remove(movie_id)
		with c2:
			if st.button("🔎", key=f"{button_prefix}_view_{movie_id}"):
				go_to("movie", movie_id)


def page_home():
	st.title("🎬 Top 25 Movies")
	top25 = movies_df.sort_values(by="popularity", ascending=False).head(25)

	cols_per_row = 5
	for i in range(0, len(top25), cols_per_row):
		row = top25.iloc[i : i + cols_per_row]
		cols = st.columns(cols_per_row)
		for col, (_, movie) in zip(cols, row.iterrows()):
			display_movie_card(movie, col, button_prefix="home")


def page_search():
	st.title("🔍 Search Movies")
	query = st.text_input("Search by title", "")
	if not query:
		st.info("Type a title to search")
		return

	matches = movies_df[movies_df["title"].str.contains(query, case=False, na=False)]
	if matches.empty:
		st.info("No movies found")
		return

	cols_per_row = 5
	for i in range(0, len(matches), cols_per_row):
		row = matches.iloc[i : i + cols_per_row]
		cols = st.columns(cols_per_row)
		for col, (_, movie) in zip(cols, row.iterrows()):
			display_movie_card(movie, col, button_prefix="search")


def page_movie():
	movie_id = st.session_state.current_movie
	if movie_id is None:
		st.error("No movie selected")
		return

	movie_rows = movies_df[movies_df["id"] == movie_id]
	if movie_rows.empty:
		st.error("Movie not found")
		return

	movie = movie_rows.iloc[0]
	st.title(movie["title"])
	if movie.get("poster") and pd.notna(movie.get("poster")):
		st.image("https://image.tmdb.org/t/p/w500" + str(movie["poster"]))

	st.write(movie.get("overview", ""))

	if movie_id not in st.session_state.liked:
		if st.button("❤️ Like"):
			st.session_state.liked.add(movie_id)
			st.success("Added to liked movies")
	else:
		if st.button("💔 Unlike"):
			st.session_state.liked.remove(movie_id)
			st.warning("Removed from liked movies")

	st.write("---")
	if st.button("🔎 Find Similar Movies"):
		similar_df = get_similar_movies(movie_id, top_n=12)
		if similar_df is None or similar_df.empty:
			st.info("No similar movies found")
		else:
			cols_per_row = 4
			for i in range(0, len(similar_df), cols_per_row):
				row = similar_df.iloc[i : i + cols_per_row]
				cols = st.columns(cols_per_row)
				for col, (_, m) in zip(cols, row.iterrows()):
					display_movie_card(m, col, button_prefix="sim")

	if st.button("⬅ Back Home"):
		go_to("home")


def page_liked():
	st.title("❤️ Liked Movies")
	liked_ids = list(st.session_state.liked)
	if not liked_ids:
		st.info("You haven't liked any movies yet.")
		return

	liked_df = movies_df[movies_df["id"].isin(liked_ids)]
	cols_per_row = 5
	for i in range(0, len(liked_df), cols_per_row):
		row = liked_df.iloc[i : i + cols_per_row]
		cols = st.columns(cols_per_row)
		for col, (_, m) in zip(cols, row.iterrows()):
			display_movie_card(m, col, button_prefix="liked")


# Sidebar navigation
st.sidebar.title("Navigation")
if st.sidebar.button("🏠 Home"):
	go_to("home")
if st.sidebar.button("🔍 Search"):
	go_to("search")
if st.sidebar.button("❤️ Liked Movies"):
	go_to("liked")


# Render pages
if st.session_state.page == "home":
	page_home()
elif st.session_state.page == "search":
	page_search()
elif st.session_state.page == "movie":
	page_movie()
elif st.session_state.page == "liked":
	page_liked()
