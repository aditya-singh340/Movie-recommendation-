
import streamlit as st
import pandas as pd
import requests
import ast
import sqlite3
from pathlib import Path

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# =====================================
# PAGE CONFIG
# =====================================

st.set_page_config(
    page_title="Movie Recommendation System",
    page_icon="🎬",
    layout="wide"
)

# =====================================
# GOOGLE LOGIN
# =====================================

if not st.user.is_logged_in:

    st.title("🎬 Movie Recommendation System")

    if st.button("🔐 Login with Google", key="google_login"):
        st.login("google")

    st.stop()


# =====================================
# API CONFIGURATION
# =====================================

API_KEY = st.secrets["TMDB_API_KEY"]

BASE_URL = "https://api.themoviedb.org/3"
IMAGE_URL = "https://image.tmdb.org/t/p/w500"


# =====================================
# DATABASE - WATCHLIST
# =====================================

def create_database():

    conn = sqlite3.connect("watchlist.db")

    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS watchlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT,
            movie_name TEXT,
            UNIQUE(user_email, movie_name)
        )
    """)

    conn.commit()
    conn.close()


create_database()


def add_to_watchlist(movie_name):

    conn = sqlite3.connect("watchlist.db")

    cursor = conn.cursor()

    cursor.execute(
        "INSERT OR IGNORE INTO watchlist (user_email, movie_name) VALUES (?, ?)",
        (st.user.email, movie_name)
    )

    conn.commit()
    conn.close()


def remove_from_watchlist(movie_name):

    conn = sqlite3.connect("watchlist.db")

    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM watchlist WHERE user_email=? AND movie_name=?",
        (st.user.email, movie_name)
    )

    conn.commit()
    conn.close()


def get_watchlist():

    conn = sqlite3.connect("watchlist.db")

    cursor = conn.cursor()

    cursor.execute(
        "SELECT movie_name FROM watchlist WHERE user_email=?",
        (st.user.email,)
    )

    result = [row[0] for row in cursor.fetchall()]

    conn.close()

    return result


# =====================================
# SIDEBAR
# =====================================

with st.sidebar:

    st.title("👤 User Profile")

    st.success(st.user.name or "User")

    st.info(st.user.email or "Email not available")

    if st.button("🚪 Logout", key="logout_button"):
        st.logout()

    st.markdown("---")

    st.subheader("🎬 Movie Menu")

    page = st.radio(
        "Select Page",
        [
            "🏠 Home",
            "🔥 Trending Movies",
            "❤️ My Watchlist",
            "🎯 Recommendations"
        ],
        key="navigation"
    )


# =====================================
# CSS
# =====================================

st.markdown("""
<style>

.stApp {
    background-color: #101010;
    color: white;
}

h1, h2, h3 {
    color: #ff4b4b;
}

div.stButton > button {
    background-color: #e50914;
    color: white;
    border-radius: 8px;
}

</style>
""", unsafe_allow_html=True)


# =====================================
# TMDB API FUNCTIONS
# =====================================

def tmdb_get(endpoint, params=None):

    if params is None:
        params = {}

    params["api_key"] = API_KEY

    try:

        response = requests.get(
            BASE_URL + endpoint,
            params=params,
            timeout=20
        )

        response.raise_for_status()

        return response.json()

    except requests.RequestException as e:

        st.error(f"TMDB API Error: {e}")

        return {}


@st.cache_data(ttl=3600)
def get_trending_movies():

    return tmdb_get("/trending/movie/week").get("results", [])


@st.cache_data(ttl=3600)
def search_tmdb_movie(movie_name):

    data = tmdb_get(
        "/search/movie",
        {"query": movie_name}
    )

    results = data.get("results", [])

    return results[0] if results else None


@st.cache_data(ttl=3600)
def get_movie_details(movie_id):

    return tmdb_get(f"/movie/{movie_id}")


@st.cache_data(ttl=3600)
def get_movie_trailer(movie_id):

    data = tmdb_get(
        f"/movie/{movie_id}/videos"
    )

    for video in data.get("results", []):

        if (
            video.get("site") == "YouTube"
            and video.get("type") == "Trailer"
        ):

            return "https://www.youtube.com/watch?v=" + video["key"]

    return None


# =====================================
# MOVIE CARD
# =====================================

def display_movie_card(movie):

    title = movie.get("title", "Unknown Movie")

    poster = movie.get("poster_path")

    if poster:

        st.image(
            IMAGE_URL + poster,
            use_container_width=True
        )

    else:

        st.info("Poster Not Available")

    st.markdown(f"### {title}")

    rating = movie.get("vote_average", 0)

    st.write(f"⭐ Rating: {rating}/10")

    movie_id = movie.get("id")

    if movie_id:

        details = get_movie_details(movie_id)

        if st.button(
            "🎬 Movie Details",
            key=f"details_{movie_id}"
        ):

            st.session_state["details_movie_id"] = movie_id

        if st.button(
            "❤️ Add to Watchlist",
            key=f"watch_{movie_id}"
        ):

            add_to_watchlist(title)

            st.success("Movie added to Watchlist!")

        trailer = get_movie_trailer(movie_id)

        if trailer:

            st.link_button(
                "▶️ Watch Trailer",
                trailer
            )


# =====================================
# SHOW MOVIE DETAILS
# =====================================

def show_movie_details(movie_id):

    details = get_movie_details(movie_id)

    if not details:

        st.warning("Movie details not available.")

        return

    st.markdown("---")

    st.header("🎬 Movie Details")

    col1, col2 = st.columns([1, 2])

    with col1:

        poster = details.get("poster_path")

        if poster:

            st.image(
                IMAGE_URL + poster,
                use_container_width=True
            )

    with col2:

        st.title(details.get("title", "Unknown"))

        st.write(
            "⭐ Rating:",
            details.get("vote_average", "N/A")
        )

        st.write(
            "📅 Release Date:",
            details.get("release_date", "N/A")
        )

        st.write(
            "⏱ Runtime:",
            str(details.get("runtime", "N/A")) + " minutes"
        )

        genres = details.get("genres", [])

        genre_names = [
            genre["name"] for genre in genres
        ]

        st.write("🎭 Genre:", ", ".join(genre_names))

        st.write("📝 Overview:")

        st.write(
            details.get("overview", "No overview available.")
        )

        trailer = get_movie_trailer(movie_id)

        if trailer:

            st.link_button(
                "▶️ Watch Movie Trailer",
                trailer
            )

        if st.button(
            "❤️ Add to Watchlist",
            key=f"detail_watch_{movie_id}"
        ):

            add_to_watchlist(
                details.get("title", "Unknown")
            )

            st.success("Added to Watchlist!")


# =====================================
# LOAD DATASET
# =====================================

@st.cache_data
def load_data():

    file_path = Path("dataset") / "cleaned_movies.csv"

    if not file_path.exists():

        return None

    return pd.read_csv(file_path)


movies = load_data()

if movies is None:

    st.error("Dataset file not found!")

    st.stop()


# =====================================
# CHECK COLUMNS
# =====================================

required_columns = [
    "title",
    "genres",
    "keywords",
    "overview",
    "cast",
    "crew"
]

missing_columns = [
    col for col in required_columns
    if col not in movies.columns
]

if missing_columns:

    st.error(f"Missing columns: {missing_columns}")

    st.stop()


# =====================================
# DATA CLEANING
# =====================================

def convert_to_list(value):

    if isinstance(value, list):

        return value

    if pd.isna(value):

        return []

    try:

        result = ast.literal_eval(str(value))

        return result if isinstance(result, list) else []

    except (ValueError, SyntaxError):

        return []


def extract_names(value):

    items = convert_to_list(value)

    names = []

    for item in items:

        if isinstance(item, dict):

            if item.get("name"):

                names.append(str(item["name"]))

        elif isinstance(item, str):

            names.append(item)

    return names


@st.cache_data
def prepare_movies(data):

    data = data.copy()

    for column in [
        "genres",
        "keywords",
        "cast",
        "crew"
    ]:

        data[column] = data[column].apply(extract_names)

    data["overview"] = (
        data["overview"].fillna("").astype(str)
    )

    data["tags"] = (

        data["genres"].apply(lambda x: " ".join(x))
        + " "
        + data["keywords"].apply(lambda x: " ".join(x))
        + " "
        + data["overview"]
        + " "
        + data["cast"].apply(lambda x: " ".join(x))
        + " "
        + data["crew"].apply(lambda x: " ".join(x))

    )

    return data


movies = prepare_movies(movies)


# =====================================
# MACHINE LEARNING
# =====================================

@st.cache_data
def create_similarity(tags):

    vectorizer = CountVectorizer(
        max_features=5000,
        stop_words="english"
    )

    vectors = vectorizer.fit_transform(tags)

    return cosine_similarity(vectors)


similarity = create_similarity(movies["tags"])


def recommend(movie_name):

    matched = movies[
        movies["title"].str.lower() == movie_name.lower()
    ]

    if matched.empty:

        return []

    movie_index = matched.index[0]

    distances = list(
        enumerate(similarity[movie_index])
    )

    distances = sorted(
        distances,
        key=lambda x: x[1],
        reverse=True
    )

    result = []

    for index, score in distances[1:]:

        title = movies.iloc[index]["title"]

        if title not in result:

            result.append(title)

        if len(result) == 5:

            break

    return result


# =====================================
# HOME PAGE
# =====================================

if page == "🏠 Home":

    st.title("🎬 Movie Recommendation System")

    st.write("Search your favourite movies!")

    # SEARCH BAR

    search_text = st.text_input(
        "🔍 Search Movie",
        placeholder="Enter movie name...",
        key="movie_search"
    )

    # GENRE FILTER

    all_genres = sorted(
        set(
            genre
            for genre_list in movies["genres"]
            for genre in genre_list
        )
    )

    selected_genre = st.selectbox(
        "🎭 Filter by Genre",
        ["All Genres"] + all_genres,
        key="genre_filter"
    )

    filtered = movies.copy()

    if search_text:

        filtered = filtered[
            filtered["title"].str.contains(
                search_text,
                case=False,
                na=False
            )
        ]

    if selected_genre != "All Genres":

        filtered = filtered[
            filtered["genres"].apply(
                lambda x: selected_genre in x
            )
        ]

    st.subheader("🎥 Movies")

    if filtered.empty:

        st.warning("No movies found!")

    else:

        movie_options = filtered["title"].tolist()

        selected_movie = st.selectbox(
            "Select Movie",
            movie_options,
            key="home_movie_selection"
        )

        if st.button(
            "🎬 Show Movie Details",
            key="home_details"
        ):

            result = search_tmdb_movie(selected_movie)

            if result:

                st.session_state["details_movie_id"] = result["id"]

            else:

                st.warning("Movie details not found.")

        if st.button(
            "❤️ Add Selected Movie to Watchlist",
            key="home_watchlist"
        ):

            add_to_watchlist(selected_movie)

            st.success("Movie added to Watchlist!")

    if "details_movie_id" in st.session_state:

        show_movie_details(
            st.session_state["details_movie_id"]
        )


# =====================================
# TRENDING MOVIES
# =====================================

elif page == "🔥 Trending Movies":

    st.title("🔥 Top 10 Trending Movies")

    trending = get_trending_movies()[:10]

    if not trending:

        st.warning("Trending movies could not be loaded.")

    else:

        for start in range(0, len(trending), 5):

            cols = st.columns(5)

            for col, movie in zip(
                cols,
                trending[start:start + 5]
            ):

                with col:

                    display_movie_card(movie)


# =====================================
# WATCHLIST
# =====================================

elif page == "❤️ My Watchlist":

    st.title("❤️ My Watchlist")

    watchlist = get_watchlist()

    if not watchlist:

        st.info("Your Watchlist is empty!")

    else:

        for index, movie_name in enumerate(watchlist):

            st.subheader(f"🎬 {movie_name}")

            col1, col2 = st.columns(2)

            with col1:

                result = search_tmdb_movie(movie_name)

                if result:

                    if result.get("poster_path"):

                        st.image(
                            IMAGE_URL + result["poster_path"],
                            width=150
                        )

            with col2:

                if st.button(
                    "❌ Remove",
                    key=f"remove_{index}"
                ):

                    remove_from_watchlist(movie_name)

                    st.rerun()

                if result:

                    if st.button(
                        "🎬 View Details",
                        key=f"watch_details_{index}"
                    ):

                        st.session_state["details_movie_id"] = result["id"]

        if "details_movie_id" in st.session_state:

            show_movie_details(
                st.session_state["details_movie_id"]
            )


# =====================================
# RECOMMENDATIONS
# =====================================

elif page == "🎯 Recommendations":

    st.title("🎯 Movie Recommendations")

    movie_list = movies["title"].dropna().tolist()

    selected_movie = st.selectbox(
        "Choose Your Favourite Movie",
        movie_list,
        key="recommend_movie"
    )

    if st.button(
        "Get Recommendations",
        key="get_recommendations"
    ):

        st.session_state["recommendations"] = recommend(
            selected_movie
        )

    if "recommendations" in st.session_state:

        recommendations = st.session_state["recommendations"]

        if recommendations:

            st.subheader("🍿 Recommended Movies")

            cols = st.columns(5)

            for col, movie_name in zip(
                cols,
                recommendations
            ):

                with col:

                    st.write(f"🎬 {movie_name}")

                    result = search_tmdb_movie(movie_name)

                    if result:

                        if result.get("poster_path"):

                            st.image(
                                IMAGE_URL + result["poster_path"],
                                use_container_width=True
                            )

                        if st.button(
                            "❤️ Add to Watchlist",
                            key=f"rec_watch_{movie_name}"
                        ):

                            add_to_watchlist(movie_name)

                            st.success("Added!")

        else:

            st.warning("No recommendations found.")


# =====================================
# FOOTER
# =====================================

st.markdown("---")

st.markdown(
    "<center>🎬 Movie Recommendation System | "
    "Python | Streamlit | Machine Learning | TMDB API</center>",
    unsafe_allow_html=True
)
