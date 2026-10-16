
import os
import pickle
import requests
import pandas as pd
import streamlit as st
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ---------------------------------------------------------------------------
# Setup: base directory for loading pickle files robustly
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# Reusable session with retries + proxy bypass
# ---------------------------------------------------------------------------
def _build_session():
    session = requests.Session()
    session.trust_env = False  # ignore system proxy settings (fixes 10054 errors)
    retries = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session

_session = _build_session()

# ---------------------------------------------------------------------------
# TMDB poster fetcher (robust)
# ---------------------------------------------------------------------------
def fetch_poster(movie_id):
    url = (
        f"https://api.themoviedb.org/3/movie/{movie_id}"
        f"?api_key=8265bd1679663a7ea12ac168da84d2e8&language=en-US"
    )
    try:
        response = _session.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        poster_path = data.get("poster_path")
        if poster_path:
            return "https://image.tmdb.org/t/p/w500/" + poster_path
        return "https://via.placeholder.com/500x750?text=No+Poster"
    except requests.exceptions.SSLError as e:
        print(f"[SSL ERROR] movie_id={movie_id}: {e}")
        return "https://via.placeholder.com/500x750?text=SSL+Error"
    except requests.exceptions.ConnectionError as e:
        print(f"[CONN ERROR] movie_id={movie_id}: {e}")
        return "https://via.placeholder.com/500x750?text=Connection+Error"
    except requests.exceptions.RequestException as e:
        print(f"[REQ ERROR] movie_id={movie_id}: {e}")
        return "https://via.placeholder.com/500x750?text=Request+Error"
    except Exception as e:
        print(f"[ERROR] movie_id={movie_id}: {e}")
        return "https://via.placeholder.com/500x750?text=Error"

# ---------------------------------------------------------------------------
# Recommendation logic
# ---------------------------------------------------------------------------
def recommend(movie):
    movie_index = movies[movies["title"] == movie].index[0]
    distances = similarity[movie_index]
    movie_list = sorted(
        list(enumerate(distances)), reverse=True, key=lambda x: x[1]
    )[1:6]

    recommended_movies = []
    recommended_movie_posters = []

    for i in movie_list:
        movie_id = movies.iloc[i[0]].movie_id
        recommended_movies.append(movies.iloc[i[0]].title)
        recommended_movie_posters.append(fetch_poster(movie_id))

    return recommended_movies, recommended_movie_posters

# ---------------------------------------------------------------------------
# Load data (absolute paths so it works no matter where streamlit is launched)
# ---------------------------------------------------------------------------
movies_dict = pickle.load(open(os.path.join(BASE_DIR, "movie_dict.pkl"), "rb"))
movies = pd.DataFrame(movies_dict)

similarity = pickle.load(open(os.path.join(BASE_DIR, "similarity.pkl"), "rb"))

# ---------------------------------------------------------------------------
# Streamlit UI
# ---------------------------------------------------------------------------
st.title("Movie Recommender System")

selected_movie_name = st.selectbox(
    "Select a movie you like:",
    movies["title"].values,
)

if st.button("Recommend"):
    names, posters = recommend(selected_movie_name)

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.text(names[0])
        st.image(posters[0])
    with col2:
        st.text(names[1])
        st.image(posters[1])
    with col3:
        st.text(names[2])
        st.image(posters[2])
    with col4:
        st.text(names[3])
        st.image(posters[3])
    with col5:
        st.text(names[4])
        st.image(posters[4])
