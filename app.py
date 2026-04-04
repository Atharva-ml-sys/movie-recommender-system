import streamlit as st
import requests
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

# =========================
# CACHE (IMPORTANT 🔥)
# =========================
@st.cache_data
def cached_fetch_movie_details(movie_name):
    return fetch_movie_details(movie_name)

@st.cache_data
def cached_fetch_poster(movie_name):
    return fetch_poster(movie_name)

# =========================
# Helper Functions
# =========================
def clean_title(title):
    # remove year
    title = title.split("(")[0]

    # remove commas style
    title = title.replace(", The", "")
    title = title.replace(", A", "")
    title = title.replace(", An", "")

    # remove extra spaces
    return title.strip()

# =========================
# Poster Fetch (FIXED 🔥)
# =========================
def fetch_poster(movie_name):
    api_key = "a0c4f6f8b557e29455901ac034a8fb10"

    try:
        clean_name = clean_title(movie_name)

        url = f"https://api.themoviedb.org/3/search/movie?api_key={api_key}&query={clean_name}"

        response = requests.get(url, timeout=5)
        data = response.json()

        best_match = None

        for movie in data.get('results', []):
            title = movie.get('title', '').lower()

            # 🔥 match logic
            if clean_name.lower() in title:
                if movie.get('poster_path'):
                    return "https://image.tmdb.org/t/p/w500/" + movie['poster_path']

            # fallback save
            if not best_match and movie.get('poster_path'):
                best_match = movie

        # 🔥 fallback best match
        if best_match:
            return "https://image.tmdb.org/t/p/w500/" + best_match['poster_path']

        return "https://via.placeholder.com/300x450?text=No+Image"

    except:
        return "https://via.placeholder.com/300x450?text=No+Image"

# =========================
# Movie Details
# =========================
def fetch_movie_details(movie_name):
    api_key = "a0c4f6f8b557e29455901ac034a8fb10"

    try:
        clean_name = clean_title(movie_name)

        url = f"https://api.themoviedb.org/3/search/movie?api_key={api_key}&query={clean_name}"

        response = requests.get(url, timeout=5)
        data = response.json()

        best_match = None

        for movie in data.get('results', []):
            title = movie.get('title', '').lower()

            if clean_name.lower() in title and movie.get('poster_path'):
                return {
                    "title": movie.get("title"),
                    "overview": movie.get("overview"),
                    "rating": movie.get("vote_average"),
                    "release_date": movie.get("release_date"),
                    "poster": "https://image.tmdb.org/t/p/w500/" + movie.get("poster_path")
                }

            if not best_match and movie.get('poster_path'):
                best_match = movie

        if best_match:
            return {
                "title": best_match.get("title"),
                "overview": best_match.get("overview"),
                "rating": best_match.get("vote_average"),
                "release_date": best_match.get("release_date"),
                "poster": "https://image.tmdb.org/t/p/w500/" + best_match.get("poster_path")
            }

        return None

    except:
        return None

# =========================
# Recommendation Logic
# =========================
def recommend_movies_by_name(movie_name, top_n=10):
    if movie_name not in user_movie_matrix.columns:
        return pd.DataFrame()

    movie_vector = user_movie_matrix[movie_name].values.reshape(1, -1)
    similarity = cosine_similarity(movie_vector, user_movie_matrix.T)[0]

    similar_movies = list(enumerate(similarity))
    similar_movies = sorted(similar_movies, key=lambda x: x[1], reverse=True)

    movie_indices = [i[0] for i in similar_movies[1:top_n+1]]

    return pd.DataFrame({
        "title": user_movie_matrix.columns[movie_indices]
    })

# =========================
# Load Data
# =========================
@st.cache_data
def load_data():
    ratings = pd.read_csv("data/raw/ratings.csv")
    movies = pd.read_csv("data/raw/movies.csv")
    return pd.merge(ratings, movies, on="movieId")

data = load_data()
data = data.sample(5000)

# =========================
# Matrix
# =========================
user_movie_matrix = data.pivot_table(
    index="userId",
    columns="title",
    values="rating"
).fillna(0)

# =========================
# UI Styling
# =========================
st.markdown("""
<style>
.movie-card {
    background-color: #111;
    padding: 10px;
    border-radius: 15px;
    text-align: center;
}
.movie-title {
    font-size: 14px;
    font-weight: bold;
    margin-top: 5px;
}
img {
    height: 250px;
    object-fit: cover;
    border-radius: 10px;
}
img:hover {
    transform: scale(1.08);
    transition: 0.2s;
    cursor: pointer;
}
</style>
""", unsafe_allow_html=True)

def get_popular_movies():
    api_key = "a0c4f6f8b557e29455901ac034a8fb10"
    
    url = f"https://api.themoviedb.org/3/movie/popular?api_key={api_key}"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        movies = []
        
        for movie in data.get('results', []):
            if movie.get('poster_path'):
                movies.append({
                    "title": movie['title'],
                    "poster": "https://image.tmdb.org/t/p/w500/" + movie['poster_path']
                })
        
        return movies[:10]  # top 10
        
    except:
        return []

# =========================
# UI
# =========================
st.title("🎬 Movie Recommendation System")

movie_list = data['title'].unique()
selected_movie = st.selectbox("🎬 Search Movie", movie_list)
top_n = st.slider("Number of recommendations", 5, 20, 10)

# =========================
# BUTTON
# =========================
if st.button("Recommend"):
    st.session_state['results'] = recommend_movies_by_name(selected_movie, top_n)

# =========================
# SHOW RESULTS (FIXED 🔥)
# =========================
results = st.session_state.get('results', None)

if results is not None:
    st.write(f"Showing {len(results)} recommendations")
    st.write("## 🎯 Recommended Movies")

    cols = st.columns(4)

    for idx, row in results.iterrows():
        poster = cached_fetch_poster(row['title'])  # 🔥 FIX

        with cols[idx % 4]:
            st.image(poster, use_container_width=True)

            if st.button("View", key=f"poster_{idx}"):
                st.session_state['selected_movie'] = row['title']
                st.rerun()

            st.markdown(f"""
                <div class="movie-card">
                    <div class="movie-title">{row['title']}</div>
                </div>
            """, unsafe_allow_html=True)

# =========================
# 🔥 POPULAR MOVIES
# =========================

st.write("## 🔥 Popular Movies")

popular_movies = get_popular_movies()

cols = st.columns(5)

for idx, movie in enumerate(popular_movies):
    with cols[idx % 5]:
        st.image(movie['poster'], use_container_width=True)
        st.caption(movie['title'])

def get_top_rated_movies():
    api_key = "a0c4f6f8b557e29455901ac034a8fb10"
    
    url = f"https://api.themoviedb.org/3/movie/top_rated?api_key={api_key}"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        movies = []
        
        for movie in data.get('results', []):
            if movie.get('poster_path'):
                movies.append({
                    "title": movie['title'],
                    "poster": "https://image.tmdb.org/t/p/w500/" + movie['poster_path']
                })
        
        return movies[:10]
        
    except:
        return []

# =========================
# ⭐ TOP RATED MOVIES
# =========================

st.write("## ⭐ Top Rated Movies")

top_movies = get_top_rated_movies()

cols = st.columns(5)

for idx, movie in enumerate(top_movies):
    with cols[idx % 5]:
        st.image(movie['poster'], use_container_width=True)
        st.caption(movie['title'])

def get_similar_movies(movie_name):
    api_key = "a0c4f6f8b557e29455901ac034a8fb10"
    
    try:
        clean_name = clean_title(movie_name)
        
        # 🔍 Step 1: search movie → get ID
        search_url = f"https://api.themoviedb.org/3/search/movie?api_key={api_key}&query={clean_name}"
        response = requests.get(search_url)
        data = response.json()
        
        if not data.get('results'):
            return []
        
        movie_id = data['results'][0]['id']
        
        # 🎯 Step 2: get similar movies
        similar_url = f"https://api.themoviedb.org/3/movie/{movie_id}/similar?api_key={api_key}"
        response = requests.get(similar_url)
        data = response.json()
        
        movies = []
        
        for movie in data.get('results', []):
            if movie.get('poster_path'):
                movies.append({
                    "title": movie['title'],
                    "poster": "https://image.tmdb.org/t/p/w500/" + movie['poster_path']
                })
        
        return movies[:10]
    
    except:
        return []

# =========================
# 🎯 SIMILAR MOVIES
# =========================

if selected_movie:
    st.write(f"## 🎯 Similar to {selected_movie}")

    similar_movies = get_similar_movies(selected_movie)

    cols = st.columns(5)

    for idx, movie in enumerate(similar_movies):
        with cols[idx % 5]:
            st.image(movie['poster'], use_container_width=True)
            st.caption(movie['title'])
        

# =========================
# SIDEBAR
# =========================
selected_movie_sidebar = st.session_state.get('selected_movie', None)

if selected_movie_sidebar:
    movie = cached_fetch_movie_details(selected_movie_sidebar)

    if movie:
        st.sidebar.title(movie['title'])

        if movie.get('poster'):
            st.sidebar.image(movie['poster'])

        st.sidebar.write(f"⭐ Rating: {movie.get('rating', 'N/A')}")
        st.sidebar.write(f"📅 Release: {movie.get('release_date', 'N/A')}")
        st.sidebar.write("📖 Overview:")
        st.sidebar.write(movie.get('overview', 'No description available'))
