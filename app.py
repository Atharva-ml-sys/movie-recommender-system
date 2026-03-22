import streamlit as st
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

# =========================
# Load Data (cached)
# =========================
@st.cache_data
def load_data():
    ratings = pd.read_csv("data/raw/ratings_small.csv")
    movies = pd.read_csv("data/raw/movies.csv")
    data = pd.merge(ratings, movies, on="movieId")
    return data

data = load_data()

# =========================
# Reduce size (IMPORTANT ⚡)
# =========================
data = data.sample(min(20000, len(data)))  # 🔥 speed hack

# =========================
# Create Matrix
# =========================
user_movie_matrix = data.pivot_table(
    index="userId",
    columns="title",
    values="rating"
)

user_movie_matrix_filled = user_movie_matrix.fillna(0)

# =========================
# Precompute similarity ONCE ⚡
# =========================
@st.cache_data
def compute_similarity(matrix):
    return cosine_similarity(matrix.values)

user_similarity = compute_similarity(user_movie_matrix_filled)

user_similarity_df = pd.DataFrame(
    user_similarity,
    index=user_movie_matrix.index,
    columns=user_movie_matrix.index
)

# =========================
# Recommendation Function
# =========================
def recommend_movies(user_id, n_recommendations=10):

    if user_id not in user_movie_matrix.index:
        return ["❌ User not found"]

    # similar users
    similar_users = user_similarity_df[user_id].sort_values(ascending=False)[1:11]
    similar_users_ids = similar_users.index

    # similar users data
    similar_users_data = data[data['userId'].isin(similar_users_ids)]

    # already watched
    user_seen_movies = data[data['userId'] == user_id]['title'].tolist()

    # filter unseen
    recommendations = similar_users_data[
        ~similar_users_data['title'].isin(user_seen_movies)
    ]

    # top movies
    recommended_movies = (
        recommendations.groupby('title')['rating']
        .mean()
        .sort_values(ascending=False)
        .head(n_recommendations)
    )

    if recommended_movies.empty:
      return ["⚠️ No recommendations found for this user"]

    return recommended_movies.reset_index()

# =========================
# UI
# =========================
st.title("🎬 Movie Recommendation System")

# Dropdown (already done)
user_id = st.selectbox("Select User ID", user_movie_matrix.index)

# Slider (STEP 3 yahi add karna hai 👇)
top_n = st.slider("Number of recommendations", 5, 20, 10)

if st.button("Recommend"):
    with st.spinner("Finding best movies for you... 🍿"):
        try:
            results = recommend_movies(user_id, top_n)

            st.write("## 🎯 Recommended Movies")

            for i, row in results.iterrows():
                st.markdown(f"""
                🎬 **{row['title']}**  
                ⭐ Rating: {row['rating']}
                """)
                st.markdown("---")

        except Exception as e:
            st.error(f"Error: {str(e)}")
    