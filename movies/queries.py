"""
Movies Use Case – CRUD Operations & Queries in Redis
-----------------------------------------------------

This script demonstrates:
• CRUD operations (Create, Read, Update, Delete)
• Recommendation-style queries
• Analytical queries on movie data
• Use of HASH, LIST, SET, and SORTED SET structures.

Implemented on data created by import.py
"""

import redis
r = redis.Redis(host="localhost", port=6379, db=0)


#############################################################
# C = CREATE
#############################################################

def create_movie(movie_id, title, release_date, genres=None, overview=""):
    """Create a new movie entry."""
    r.hset(f"movie:{movie_id}", mapping={
        "title": title,
        "release_date": release_date,
        "overview": overview,
        "vote_average": 0,
        "vote_count": 0
    })

    # Add genres
    if genres:
        for genre in genres:
            r.sadd(f"movie:{movie_id}:genres", genre)
            r.sadd(f"genre:{genre.lower()}:movies", movie_id)

    r.sadd("movie:all", movie_id)
    print(f"Movie '{title}' (ID: {movie_id}) created.")


def add_rating(user_id, movie_id, rating):
    """Add or update a user's rating for a movie."""
    # Store in user's ratings
    r.zadd(f"user:{user_id}:ratings", {movie_id: rating})

    # Store in movie's ratings
    r.zadd(f"movie:{movie_id}:ratings", {user_id: rating})

    # Create user if not exists
    r.hsetnx(f"user:{user_id}", "user_id", user_id)
    r.sadd("user:all", user_id)

    # Update movie's average rating
    update_movie_rating_stats(movie_id)

    print(f"User {user_id} rated movie {movie_id} with {rating} stars.")


def add_to_watchlist(user_id, movie_id):
    """Add a movie to user's watchlist."""
    r.sadd(f"user:{user_id}:watchlist", movie_id)
    print(f"Movie {movie_id} added to user {user_id}'s watchlist.")


#############################################################
# R = READ
#############################################################

def get_movie(movie_id):
    """Retrieve movie details."""
    data = r.hgetall(f"movie:{movie_id}")
    return {k.decode(): v.decode() for k, v in data.items()}


def get_movie_genres(movie_id):
    """Get genres of a movie."""
    return [g.decode() for g in r.smembers(f"movie:{movie_id}:genres")]


def get_movie_cast(movie_id, limit=10):
    """Get cast of a movie."""
    return [a.decode() for a in r.lrange(f"movie:{movie_id}:cast", 0, limit-1)]


def get_movie_crew(movie_id):
    """Get crew of a movie (director, etc.)."""
    return [c.decode() for c in r.lrange(f"movie:{movie_id}:crew", 0, -1)]


def get_movie_ratings(movie_id, limit=10):
    """Get user ratings for a movie."""
    ratings = r.zrevrange(f"movie:{movie_id}:ratings", 0, limit-1, withscores=True)
    return [(user_id.decode(), score) for user_id, score in ratings]


def get_user_ratings(user_id, limit=10):
    """Get movies rated by a user."""
    ratings = r.zrevrange(f"user:{user_id}:ratings", 0, limit-1, withscores=True)
    return [(movie_id.decode(), score) for movie_id, score in ratings]


def get_user_watchlist(user_id):
    """Get user's watchlist."""
    return [m.decode() for m in r.smembers(f"user:{user_id}:watchlist")]


def get_movies_by_genre(genre, limit=20):
    """Get all movies of a specific genre."""
    return [m.decode() for m in r.srandmember(f"genre:{genre.lower()}:movies", limit)]


def get_movies_by_actor(actor_name, limit=20):
    """Get all movies featuring a specific actor."""
    key = f"actor:{actor_name.lower().replace(' ', '_')}:movies"
    return [m.decode() for m in r.smembers(key)]


def get_movies_by_director(director_name, limit=20):
    """Get all movies by a specific director."""
    key = f"director:{director_name.lower().replace(' ', '_')}:movies"
    return [m.decode() for m in r.smembers(key)]


def get_movie_by_imdb(imdb_id):
    """Get movie by IMDB ID (e.g., 'tt0114709')."""
    if not imdb_id.startswith("tt"):
        imdb_id = f"tt{imdb_id}"
    movie_id = r.get(f"imdb:{imdb_id}")
    if movie_id:
        return get_movie(movie_id.decode())
    return None


def get_movie_by_tmdb(tmdb_id):
    """Get movie by TMDB ID."""
    movie_id = r.get(f"tmdb:{tmdb_id}")
    if movie_id:
        return get_movie(movie_id.decode())
    return None


def get_movie_keywords(movie_id):
    """Get keywords of a movie."""
    return [k.decode() for k in r.smembers(f"movie:{movie_id}:keywords")]


#############################################################
# U = UPDATE
#############################################################

def update_movie(movie_id, **fields):
    """Update movie fields."""
    if fields:
        r.hset(f"movie:{movie_id}", mapping=fields)
        print(f"Movie {movie_id} updated: {list(fields.keys())}")


def update_movie_rating_stats(movie_id):
    """Recalculate and update movie's rating statistics."""
    ratings = r.zrange(f"movie:{movie_id}:ratings", 0, -1, withscores=True)
    if ratings:
        total = sum(score for _, score in ratings)
        count = len(ratings)
        avg = total / count

        r.hset(f"movie:{movie_id}", mapping={
            "user_rating_avg": round(avg, 2),
            "user_rating_count": count
        })

        # Update ranking
        if count >= 5:
            r.zadd("movie:top_rated", {movie_id: avg})


#############################################################
# D = DELETE
#############################################################

def delete_movie(movie_id):
    """Delete a movie and all its associated data."""
    # Get genres to clean up genre index
    genres = get_movie_genres(movie_id)
    for genre in genres:
        r.srem(f"genre:{genre.lower()}:movies", movie_id)

    # Remove from indexes
    r.srem("movie:all", movie_id)
    r.zrem("movie:top_rated", movie_id)
    r.zrem("movie:popular", movie_id)

    # Delete all associated keys
    r.delete(f"movie:{movie_id}")
    r.delete(f"movie:{movie_id}:genres")
    r.delete(f"movie:{movie_id}:cast")
    r.delete(f"movie:{movie_id}:crew")
    r.delete(f"movie:{movie_id}:ratings")
    r.delete(f"movie:{movie_id}:keywords")

    print(f"Movie {movie_id} and all associated data deleted.")


def delete_rating(user_id, movie_id):
    """Remove a user's rating for a movie."""
    r.zrem(f"user:{user_id}:ratings", movie_id)
    r.zrem(f"movie:{movie_id}:ratings", user_id)
    update_movie_rating_stats(movie_id)
    print(f"Rating from user {user_id} for movie {movie_id} deleted.")


def remove_from_watchlist(user_id, movie_id):
    """Remove a movie from user's watchlist."""
    r.srem(f"user:{user_id}:watchlist", movie_id)
    print(f"Movie {movie_id} removed from user {user_id}'s watchlist.")


#############################################################
# ANALYTICAL QUERIES
#############################################################

def top_rated_movies(n=10):
    """Get top rated movies."""
    print(f"\nTop {n} rated movies:")
    results = r.zrevrange("movie:top_rated", 0, n-1, withscores=True)
    for movie_id, rating in results:
        movie = get_movie(movie_id.decode())
        title = movie.get("title", "Unknown")
        print(f"  {rating:.1f} - {title} (ID: {movie_id.decode()})")
    return results


def most_popular_movies(n=10):
    """Get most popular movies (by popularity score)."""
    print(f"\nTop {n} most popular movies:")
    results = r.zrevrange("movie:popular", 0, n-1, withscores=True)
    for movie_id, popularity in results:
        movie = get_movie(movie_id.decode())
        title = movie.get("title", "Unknown")
        print(f"  {popularity:.1f} - {title}")
    return results


def get_movie_count():
    """Get total number of movies."""
    return r.scard("movie:all")


def get_user_count():
    """Get total number of users."""
    return r.scard("user:all")


def get_genre_stats():
    """Get movie count per genre."""
    print("\nMovies per genre:")
    genres = ["action", "comedy", "drama", "thriller", "sci-fi", "romance", "horror", "adventure"]
    for genre in genres:
        count = r.scard(f"genre:{genre}:movies")
        if count > 0:
            print(f"  {genre.title()}: {count} movies")


def recommend_by_genre(user_id, limit=5):
    """Simple genre-based recommendation: find movies in genres the user likes."""
    print(f"\nRecommendations for user {user_id}:")

    # Get user's highly rated movies (rating >= 4)
    user_ratings = r.zrangebyscore(f"user:{user_id}:ratings", 4, 5)

    if not user_ratings:
        print("  No ratings found for recommendations.")
        return []

    # Collect genres from liked movies
    liked_genres = set()
    for movie_id in user_ratings:
        genres = r.smembers(f"movie:{movie_id.decode()}:genres")
        liked_genres.update(g.decode().lower() for g in genres)

    # Find movies in those genres that user hasn't rated
    recommendations = set()
    for genre in liked_genres:
        genre_movies = r.smembers(f"genre:{genre}:movies")
        for movie_id in genre_movies:
            # Check if user already rated this movie
            if not r.zscore(f"user:{user_id}:ratings", movie_id):
                recommendations.add(movie_id.decode())
                if len(recommendations) >= limit:
                    break
        if len(recommendations) >= limit:
            break

    # Print recommendations with details
    for movie_id in list(recommendations)[:limit]:
        movie = get_movie(movie_id)
        title = movie.get("title", "Unknown")
        rating = movie.get("vote_average", "N/A")
        print(f"  - {title} (Rating: {rating})")

    return list(recommendations)


def find_similar_movies(movie_id, limit=5):
    """Find movies similar to a given movie (same genres)."""
    print(f"\nMovies similar to movie {movie_id}:")

    # Get genres of the source movie
    source_genres = get_movie_genres(movie_id)
    if not source_genres:
        print("  No genre information available.")
        return []

    # Find movies with overlapping genres
    similar = {}
    for genre in source_genres:
        genre_movies = r.smembers(f"genre:{genre.lower()}:movies")
        for mid in genre_movies:
            mid = mid.decode()
            if mid != str(movie_id):
                similar[mid] = similar.get(mid, 0) + 1

    # Sort by number of matching genres
    sorted_similar = sorted(similar.items(), key=lambda x: -x[1])[:limit]

    for mid, match_count in sorted_similar:
        movie = get_movie(mid)
        title = movie.get("title", "Unknown")
        print(f"  - {title} ({match_count} matching genres)")

    return [m[0] for m in sorted_similar]


#############################################################

if __name__ == "__main__":
    print("=" * 50)
    print("Movies Use Case - Queries Demo")
    print("=" * 50)

    # Statistics
    movie_count = get_movie_count()
    user_count = get_user_count()
    print(f"\nTotal movies: {movie_count}")
    print(f"Total users: {user_count}")

    # Genre stats
    get_genre_stats()

    # Top movies
    top_rated_movies(5)
    most_popular_movies(5)

    # Example: Get specific movie info
    print("\n" + "-" * 50)
    print("Example: Movie Details (ID: 1)")
    print("-" * 50)

    movie = get_movie("1")
    if movie:
        print(f"Title: {movie.get('title', 'N/A')}")
        print(f"Release: {movie.get('release_date', 'N/A')}")
        print(f"Rating: {movie.get('vote_average', 'N/A')}")
        print(f"Genres: {get_movie_genres('1')}")
        print(f"Cast: {get_movie_cast('1', 5)}")
        print(f"Crew: {get_movie_crew('1')}")

    # Recommendations
    recommend_by_genre("1", limit=3)

    # Similar movies
    find_similar_movies("1", limit=3)

    # CRUD Demo
    print("\n" + "-" * 50)
    print("CRUD Demo")
    print("-" * 50)

    # Create
    create_movie("99999", "Test Movie", "2024-01-01", genres=["Drama", "Comedy"])

    # Read
    print(f"Movie 99999: {get_movie('99999')}")

    # Add rating
    add_rating("999", "99999", 4.5)

    # Update
    update_movie("99999", overview="This is an updated description.")
    print(f"After update: {get_movie('99999')}")

    # Watchlist
    add_to_watchlist("999", "99999")
    print(f"Watchlist: {get_user_watchlist('999')}")

    # Delete
    delete_movie("99999")
    print(f"After delete: {get_movie('99999')}")
