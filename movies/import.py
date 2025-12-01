"""
Movies Use Case – Data Import into Redis
-----------------------------------------

This script imports The Movies Dataset into Redis
using a well-defined data model based on HASH, LIST, SET, and SORTED SET structures.

Data Model implemented here:
• movie:<movie_id>                -> HASH containing movie metadata
• movie:<movie_id>:cast           -> LIST of actor names
• movie:<movie_id>:crew           -> LIST of crew members (director, etc.)
• movie:<movie_id>:genres         -> SET of genre names
• movie:<movie_id>:ratings        -> SORTED SET (user_id as member, rating as score)
• user:<user_id>                  -> HASH containing user info
• user:<user_id>:ratings          -> SORTED SET (movie_id as member, rating as score)
• genre:<genre_name>:movies       -> SET of movie IDs per genre
• movie:top_rated                 -> SORTED SET ranking movies by avg rating
• movie:popular                   -> SORTED SET ranking movies by number of ratings

This script demonstrates:
• CREATE operations (HSET, LPUSH, SADD, ZADD)
• Modeling relational data (movies, users, ratings) in Redis
• Building indexes for efficient queries (genre index, rankings)
"""

import csv
import redis
import os
import json
import ast

# Connect to Redis
r = redis.Redis(host="localhost", port=6379, db=0)

# Path to CSV data
DATA_PATH = os.path.join(os.path.dirname(__file__), "data")

# Batch size for pipeline operations
BATCH_SIZE = 5000


#############################################################
# 1. Import Movies Metadata
#############################################################

def import_movies(limit=None):
    """Import movie metadata from movies_metadata.csv."""
    path = os.path.join(DATA_PATH, "movies_metadata.csv")

    if not os.path.exists(path):
        print(f"Error: {path} not found. Please download The Movies Dataset from Kaggle.")
        return

    print("Importing movies...")
    count = 0

    pipe = r.pipeline()
    pipe_count = 0

    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if limit and count >= limit:
                break

            try:
                movie_id = row.get("id", "")
                if not movie_id or not movie_id.isdigit():
                    continue

                # Parse genres (stored as JSON-like string)
                genres = []
                try:
                    genres_data = ast.literal_eval(row.get("genres", "[]"))
                    genres = [g["name"] for g in genres_data if "name" in g]
                except:
                    pass

                # Movie HASH
                pipe.hset(f"movie:{movie_id}", mapping={
                    "title": row.get("title", ""),
                    "original_title": row.get("original_title", ""),
                    "release_date": row.get("release_date", ""),
                    "budget": row.get("budget", "0"),
                    "revenue": row.get("revenue", "0"),
                    "runtime": row.get("runtime", "0"),
                    "vote_average": row.get("vote_average", "0"),
                    "vote_count": row.get("vote_count", "0"),
                    "popularity": row.get("popularity", "0"),
                    "overview": row.get("overview", "")[:500],  # Truncate long descriptions
                    "language": row.get("original_language", ""),
                    "status": row.get("status", "")
                })
                pipe_count += 1

                # Store genres as SET and create genre index
                for genre in genres:
                    pipe.sadd(f"movie:{movie_id}:genres", genre)
                    pipe.sadd(f"genre:{genre.lower()}:movies", movie_id)
                    pipe_count += 2

                # Add to movie index
                pipe.sadd("movie:all", movie_id)
                pipe_count += 1

                # Add to popularity ranking
                try:
                    popularity = float(row.get("popularity", 0))
                    pipe.zadd("movie:popular", {movie_id: popularity})
                    pipe_count += 1
                except:
                    pass

                # Add to rating ranking (from vote_average)
                try:
                    vote_avg = float(row.get("vote_average", 0))
                    vote_count = int(float(row.get("vote_count", 0)))
                    if vote_count >= 10:  # Only include movies with enough votes
                        pipe.zadd("movie:top_rated", {movie_id: vote_avg})
                        pipe_count += 1
                except:
                    pass

                count += 1

                # Execute pipeline in batches
                if pipe_count >= BATCH_SIZE:
                    pipe.execute()
                    pipe = r.pipeline()
                    pipe_count = 0
                    print(f"  -> {count} movies imported...")

            except Exception as e:
                continue

    # Execute remaining
    if pipe_count > 0:
        pipe.execute()

    print(f"  -> {count} movies imported.")


#############################################################
# 2. Import Credits (Cast & Crew)
#############################################################

def import_credits(limit=None):
    """Import cast and crew information from credits.csv."""
    path = os.path.join(DATA_PATH, "credits.csv")

    if not os.path.exists(path):
        print("Credits file not found, skipping...")
        return

    print("Importing credits...")
    count = 0

    pipe = r.pipeline()
    pipe_count = 0

    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if limit and count >= limit:
                break

            try:
                movie_id = row.get("id", "")
                if not movie_id:
                    continue

                # Parse cast
                try:
                    cast_data = ast.literal_eval(row.get("cast", "[]"))
                    for actor in cast_data[:10]:  # Top 10 actors
                        if "name" in actor:
                            pipe.lpush(f"movie:{movie_id}:cast", actor["name"])
                            # Create actor index
                            pipe.sadd(f"actor:{actor['name'].lower().replace(' ', '_')}:movies", movie_id)
                            pipe_count += 2
                except:
                    pass

                # Parse crew (focus on director)
                try:
                    crew_data = ast.literal_eval(row.get("crew", "[]"))
                    for member in crew_data:
                        if member.get("job") == "Director":
                            pipe.lpush(f"movie:{movie_id}:crew", f"Director: {member['name']}")
                            # Create director index
                            pipe.sadd(f"director:{member['name'].lower().replace(' ', '_')}:movies", movie_id)
                            pipe_count += 2
                except:
                    pass

                count += 1

                # Execute pipeline in batches
                if pipe_count >= BATCH_SIZE:
                    pipe.execute()
                    pipe = r.pipeline()
                    pipe_count = 0
                    print(f"  -> {count} credits imported...")

            except Exception as e:
                continue

    # Execute remaining
    if pipe_count > 0:
        pipe.execute()

    print(f"  -> {count} credits imported.")


#############################################################
# 3. Import Ratings
#############################################################

def import_ratings(limit=None, batch_size=10000):
    """Import user ratings from ratings.csv."""
    path = os.path.join(DATA_PATH, "ratings.csv")

    if not os.path.exists(path):
        path = os.path.join(DATA_PATH, "ratings_small.csv")
        if not os.path.exists(path):
            print("Error: Ratings file not found. Please download ratings.csv or ratings_small.csv from Kaggle.")
            return

    print("Importing ratings...")
    count = 0
    rating_sums = {}
    rating_counts = {}
    user_ratings = {}  # Track rating counts per user

    pipe = r.pipeline()
    pipe_count = 0

    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if limit and count >= limit:
                break

            try:
                user_id = row.get("userId", "")
                movie_id = row.get("movieId", "")
                rating = float(row.get("rating", 0))

                if not user_id or not movie_id:
                    continue

                # Add to pipeline
                pipe.zadd(f"user:{user_id}:ratings", {movie_id: rating})
                pipe.zadd(f"movie:{movie_id}:ratings", {user_id: rating})
                pipe_count += 2

                # Track for average calculation
                if movie_id not in rating_sums:
                    rating_sums[movie_id] = 0.0
                    rating_counts[movie_id] = 0
                rating_sums[movie_id] += rating
                rating_counts[movie_id] += 1

                # Track user rating count
                user_ratings[user_id] = user_ratings.get(user_id, 0) + 1

                count += 1

                # Execute pipeline in batches
                if pipe_count >= batch_size:
                    pipe.execute()
                    pipe = r.pipeline()
                    pipe_count = 0
                    if count % 500000 == 0:
                        print(f"  -> {count} ratings imported...")

            except Exception:
                continue

    # Execute remaining
    if pipe_count > 0:
        pipe.execute()

    # Update user stats (batched)
    print(f"  -> Updating {len(user_ratings)} user statistics...")
    pipe = r.pipeline()
    pipe_count = 0
    for user_id, rating_count in user_ratings.items():
        pipe.hset(f"user:{user_id}", mapping={"user_id": user_id, "rating_count": rating_count})
        pipe.sadd("user:all", user_id)
        pipe_count += 2
        if pipe_count >= batch_size:
            pipe.execute()
            pipe = r.pipeline()
            pipe_count = 0
    if pipe_count > 0:
        pipe.execute()

    # Update movie ratings (batched)
    print(f"  -> Updating {len(rating_sums)} movie statistics...")
    pipe = r.pipeline()
    pipe_count = 0
    for movie_id, total in rating_sums.items():
        if rating_counts[movie_id] >= 5:
            avg_rating = total / rating_counts[movie_id]
            pipe.zadd("movie:top_rated", {movie_id: avg_rating})
            pipe.hset(f"movie:{movie_id}", mapping={
                "user_rating_avg": round(avg_rating, 2),
                "user_rating_count": rating_counts[movie_id]
            })
            pipe_count += 2
            if pipe_count >= batch_size:
                pipe.execute()
                pipe = r.pipeline()
                pipe_count = 0
    if pipe_count > 0:
        pipe.execute()

    print(f"  -> {count} ratings imported.")


#############################################################
# 4. Import Keywords
#############################################################

def import_keywords(limit=None):
    """Import movie keywords from keywords.csv."""
    path = os.path.join(DATA_PATH, "keywords.csv")

    if not os.path.exists(path):
        print("Keywords file not found, skipping...")
        return

    print("Importing keywords...")
    count = 0

    pipe = r.pipeline()
    pipe_count = 0

    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if limit and count >= limit:
                break

            try:
                movie_id = row.get("id", "")
                keywords_data = ast.literal_eval(row.get("keywords", "[]"))

                for kw in keywords_data[:20]:  # Limit keywords per movie
                    if "name" in kw:
                        pipe.sadd(f"movie:{movie_id}:keywords", kw["name"])
                        pipe_count += 1

                count += 1

                # Execute pipeline in batches
                if pipe_count >= BATCH_SIZE:
                    pipe.execute()
                    pipe = r.pipeline()
                    pipe_count = 0

            except Exception as e:
                continue

    # Execute remaining
    if pipe_count > 0:
        pipe.execute()

    print(f"  -> {count} keyword sets imported.")


#############################################################
# 5. Import Links (IMDB/TMDB IDs)
#############################################################

def import_links():
    """Import IMDB and TMDB links from links.csv."""
    path = os.path.join(DATA_PATH, "links.csv")

    if not os.path.exists(path):
        path = os.path.join(DATA_PATH, "links_small.csv")
        if not os.path.exists(path):
            print("Links file not found, skipping...")
            return

    print("Importing links...")
    count = 0

    pipe = r.pipeline()
    pipe_count = 0

    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                movie_id = row.get("movieId", "")
                imdb_id = row.get("imdbId", "")
                tmdb_id = row.get("tmdbId", "")

                if not movie_id:
                    continue

                # Add IMDB/TMDB IDs to movie hash
                mapping = {}
                if imdb_id:
                    mapping["imdb_id"] = f"tt{imdb_id}"
                    pipe.set(f"imdb:tt{imdb_id}", movie_id)
                    pipe_count += 1
                if tmdb_id:
                    mapping["tmdb_id"] = tmdb_id
                    pipe.set(f"tmdb:{tmdb_id}", movie_id)
                    pipe_count += 1

                if mapping:
                    pipe.hset(f"movie:{movie_id}", mapping=mapping)
                    pipe_count += 1

                count += 1

                # Execute pipeline in batches
                if pipe_count >= BATCH_SIZE:
                    pipe.execute()
                    pipe = r.pipeline()
                    pipe_count = 0

            except Exception:
                continue

    # Execute remaining
    if pipe_count > 0:
        pipe.execute()

    print(f"  -> {count} links imported.")


#############################################################

if __name__ == "__main__":
    print("=" * 50)
    print("Movies Use Case - Data Import")
    print("=" * 50)

    print("\nStep 1: Importing movies...")
    import_movies()

    print("\nStep 2: Importing credits...")
    import_credits()

    print("\nStep 3: Importing ratings...")
    import_ratings()

    print("\nStep 4: Importing keywords...")
    import_keywords()

    print("\nStep 5: Importing links...")
    import_links()

    print("\n" + "=" * 50)
    print("Import finished successfully!")
    print("=" * 50)
