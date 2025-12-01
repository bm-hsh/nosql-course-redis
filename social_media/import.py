"""
Social Media Use Case – Data Import into Redis
-----------------------------------------------

This script imports the Social Media Sentiment Analysis dataset into Redis
using a well-defined data model based on HASH, LIST, SET, and SORTED SET structures.

Data Model implemented here:
• post:<post_id>                  -> HASH containing post content and metadata
• post:<post_id>:hashtags         -> SET of hashtags used in the post
• social:user:<user_id>           -> HASH containing user info
• social:user:<user_id>:posts     -> LIST of post IDs by this user
• social:user:all                 -> SET of all user IDs
• hashtag:<tag>:posts             -> SET of post IDs using this hashtag
• platform:<name>:posts           -> SET of post IDs per platform
• country:<code>:posts            -> SET of post IDs per country
• sentiment:<type>:posts          -> SET of post IDs per sentiment type
• post:trending                   -> SORTED SET ranking posts by engagement
• hashtag:trending                -> SORTED SET ranking hashtags by usage count

This script demonstrates:
• CREATE operations (HSET, LPUSH, SADD, ZADD, ZINCRBY)
• Indexing for multi-dimensional queries (platform, country, sentiment, hashtag)
• Engagement tracking and trending content
"""

import csv
import redis
import os
import re
from datetime import datetime

# Connect to Redis
r = redis.Redis(host="localhost", port=6379, db=0)

# Path to CSV data
DATA_PATH = os.path.join(os.path.dirname(__file__), "data")

# Batch size for pipeline operations
BATCH_SIZE = 5000


#############################################################
# Helper Functions
#############################################################

def extract_hashtags(text):
    """Extract hashtags from post content."""
    if not text:
        return []
    return re.findall(r'#(\w+)', text.lower())


def calculate_engagement(likes, retweets):
    """Calculate engagement score."""
    try:
        return int(likes) + int(retweets) * 2  # Retweets weighted more
    except:
        return 0


#############################################################
# 1. Import Posts
#############################################################

def import_posts(limit=None):
    """Import social media posts from the dataset."""
    path = os.path.join(DATA_PATH, "sentimentdataset.csv")

    if not os.path.exists(path):
        print(f"Error: {path} not found. Please download the Sentiment Analysis dataset.")
        return

    print("Importing posts...")
    count = 0
    hashtag_counts = {}
    user_ids = set()
    user_posts = {}  # Track posts per user for final update

    pipe = r.pipeline()
    pipe_count = 0

    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if limit and count >= limit:
                break

            try:
                post_id = str(count + 1)

                # Extract fields (adjust column names based on actual dataset)
                text = row.get("Text", row.get("text", row.get("content", "")))
                timestamp = row.get("Timestamp", row.get("timestamp", row.get("date", "")))
                platform = row.get("Platform", row.get("platform", "unknown"))
                country = row.get("Country", row.get("country", "unknown"))
                likes = row.get("Likes", row.get("likes", "0"))
                retweets = row.get("Retweets", row.get("retweets", row.get("shares", "0")))
                sentiment = row.get("Sentiment", row.get("sentiment", "neutral"))
                user_id = row.get("User", row.get("user_id", row.get("user", f"user_{count % 1000}")))

                # Clean values
                platform = platform.strip().lower() if platform else "unknown"
                country = country.strip().lower() if country else "unknown"
                sentiment = sentiment.strip().lower() if sentiment else "neutral"

                # Calculate engagement
                engagement = calculate_engagement(likes, retweets)

                # Post HASH
                pipe.hset(f"post:{post_id}", mapping={
                    "text": text[:500] if text else "",  # Truncate long posts
                    "timestamp": timestamp,
                    "platform": platform,
                    "country": country,
                    "likes": likes,
                    "retweets": retweets,
                    "sentiment": sentiment,
                    "user_id": user_id,
                    "engagement": engagement
                })
                pipe_count += 1

                # Extract hashtags (from column or from text)
                hashtags_col = row.get("Hashtags", row.get("hashtags", ""))
                if hashtags_col and hashtags_col.strip():
                    # Parse hashtags from column (comma or space separated)
                    hashtags = [h.strip().strip('#').lower() for h in re.split(r'[,\s]+', hashtags_col) if h.strip()]
                else:
                    # Fallback: extract from text
                    hashtags = extract_hashtags(text)

                for tag in hashtags:
                    pipe.sadd(f"post:{post_id}:hashtags", tag)
                    pipe.sadd(f"hashtag:{tag}:posts", post_id)
                    pipe_count += 2
                    # Track hashtag frequency
                    hashtag_counts[tag] = hashtag_counts.get(tag, 0) + 1

                # Link post to user
                pipe.lpush(f"social:user:{user_id}:posts", post_id)
                pipe_count += 1
                user_ids.add(user_id)
                user_posts[user_id] = user_posts.get(user_id, 0) + 1

                # Create indexes
                pipe.sadd(f"platform:{platform}:posts", post_id)
                pipe.sadd(f"country:{country}:posts", post_id)
                pipe.sadd(f"sentiment:{sentiment}:posts", post_id)
                pipe_count += 3

                # Add to trending (by engagement)
                if engagement > 0:
                    pipe.zadd("post:trending", {post_id: engagement})
                    pipe_count += 1

                # Add to post index
                pipe.sadd("post:all", post_id)
                pipe_count += 1

                count += 1

                # Execute pipeline in batches
                if pipe_count >= BATCH_SIZE:
                    pipe.execute()
                    pipe = r.pipeline()
                    pipe_count = 0
                    print(f"  -> {count} posts imported...")

            except Exception as e:
                continue

    # Execute remaining items in pipeline
    if pipe_count > 0:
        pipe.execute()

    # Store hashtag frequencies and user entries (smaller dataset, single pipeline)
    pipe = r.pipeline()
    for tag, freq in hashtag_counts.items():
        pipe.zadd("hashtag:trending", {tag: freq})

    for user_id in user_ids:
        pipe.hset(f"social:user:{user_id}", mapping={
            "user_id": user_id,
            "post_count": user_posts.get(user_id, 0)
        })
        pipe.sadd("social:user:all", user_id)
    pipe.execute()

    print(f"  -> {count} posts imported.")
    print(f"  -> {len(user_ids)} users created.")
    print(f"  -> {len(hashtag_counts)} unique hashtags indexed.")


#############################################################

if __name__ == "__main__":
    print("=" * 50)
    print("Social Media Use Case - Data Import")
    print("=" * 50)

    print("\nImporting posts...")
    import_posts()

    print("\n" + "=" * 50)
    print("Import finished successfully!")
    print("=" * 50)
