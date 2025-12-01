"""
Social Media Use Case – CRUD Operations & Queries in Redis
-----------------------------------------------------------

This script demonstrates:
• CRUD operations (Create, Read, Update, Delete)
• Trending content queries (posts, hashtags)
• Sentiment analysis queries
• Platform and geographic analytics
• Use of HASH, LIST, SET, and SORTED SET structures.

Implemented on data created by import.py
"""

import redis
import re
from datetime import datetime

r = redis.Redis(host="localhost", port=6379, db=0)


def extract_hashtags(text):
    """Extract hashtags from post content."""
    if not text:
        return []
    return re.findall(r'#(\w+)', text.lower())


#############################################################
# C = CREATE
#############################################################

def create_post(post_id, user_id, text, platform="twitter", country="unknown", sentiment="neutral"):
    """Create a new social media post."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Post HASH
    r.hset(f"post:{post_id}", mapping={
        "text": text[:500],
        "timestamp": timestamp,
        "platform": platform.lower(),
        "country": country.lower(),
        "likes": 0,
        "retweets": 0,
        "sentiment": sentiment.lower(),
        "user_id": user_id,
        "engagement": 0
    })

    # Extract and store hashtags
    hashtags = extract_hashtags(text)
    for tag in hashtags:
        r.sadd(f"post:{post_id}:hashtags", tag)
        r.sadd(f"hashtag:{tag}:posts", post_id)
        r.zincrby("hashtag:trending", 1, tag)

    # Link to user
    r.lpush(f"social:user:{user_id}:posts", post_id)
    r.hincrby(f"social:user:{user_id}", "post_count", 1)

    # Create indexes
    r.sadd(f"platform:{platform.lower()}:posts", post_id)
    r.sadd(f"country:{country.lower()}:posts", post_id)
    r.sadd(f"sentiment:{sentiment.lower()}:posts", post_id)
    r.sadd("post:all", post_id)

    print(f"Post {post_id} created by user {user_id}.")


def create_user(user_id, username=None):
    """Create a new user."""
    r.hset(f"social:user:{user_id}", mapping={
        "user_id": user_id,
        "username": username or user_id,
        "post_count": 0,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    r.sadd("social:user:all", user_id)
    print(f"User {user_id} created.")


#############################################################
# R = READ
#############################################################

def get_post(post_id):
    """Retrieve a post by ID."""
    data = r.hgetall(f"post:{post_id}")
    return {k.decode(): v.decode() for k, v in data.items()}


def get_post_hashtags(post_id):
    """Get hashtags of a post."""
    return [h.decode() for h in r.smembers(f"post:{post_id}:hashtags")]


def get_user(user_id):
    """Retrieve user info."""
    data = r.hgetall(f"social:user:{user_id}")
    return {k.decode(): v.decode() for k, v in data.items()}


def get_user_posts(user_id, limit=10):
    """Get posts by a user."""
    post_ids = r.lrange(f"social:user:{user_id}:posts", 0, limit-1)
    return [pid.decode() for pid in post_ids]


def get_posts_by_hashtag(hashtag, limit=20):
    """Get all posts with a specific hashtag."""
    return [p.decode() for p in r.srandmember(f"hashtag:{hashtag.lower()}:posts", limit)]


def get_posts_by_platform(platform, limit=20):
    """Get posts from a specific platform."""
    return [p.decode() for p in r.srandmember(f"platform:{platform.lower()}:posts", limit)]


def get_posts_by_country(country, limit=20):
    """Get posts from a specific country."""
    return [p.decode() for p in r.srandmember(f"country:{country.lower()}:posts", limit)]


def get_posts_by_sentiment(sentiment, limit=20):
    """Get posts with a specific sentiment."""
    return [p.decode() for p in r.srandmember(f"sentiment:{sentiment.lower()}:posts", limit)]


#############################################################
# U = UPDATE
#############################################################

def like_post(post_id):
    """Increment likes on a post."""
    r.hincrby(f"post:{post_id}", "likes", 1)
    update_engagement(post_id)
    print(f"Post {post_id} liked.")


def retweet_post(post_id):
    """Increment retweets on a post."""
    r.hincrby(f"post:{post_id}", "retweets", 1)
    update_engagement(post_id)
    print(f"Post {post_id} retweeted.")


def update_engagement(post_id):
    """Recalculate and update engagement score."""
    post = get_post(post_id)
    likes = int(post.get("likes", 0))
    retweets = int(post.get("retweets", 0))
    engagement = likes + retweets * 2

    r.hset(f"post:{post_id}", "engagement", engagement)
    r.zadd("post:trending", {post_id: engagement})


def update_post_sentiment(post_id, new_sentiment):
    """Update the sentiment of a post."""
    old_sentiment = r.hget(f"post:{post_id}", "sentiment")
    if old_sentiment:
        r.srem(f"sentiment:{old_sentiment.decode()}:posts", post_id)

    r.hset(f"post:{post_id}", "sentiment", new_sentiment.lower())
    r.sadd(f"sentiment:{new_sentiment.lower()}:posts", post_id)
    print(f"Post {post_id} sentiment updated to '{new_sentiment}'.")


#############################################################
# D = DELETE
#############################################################

def delete_post(post_id):
    """Delete a post and clean up all indexes."""
    post = get_post(post_id)
    if not post:
        print(f"Post {post_id} not found.")
        return

    user_id = post.get("user_id")
    platform = post.get("platform")
    country = post.get("country")
    sentiment = post.get("sentiment")

    # Remove from user's posts
    if user_id:
        r.lrem(f"social:user:{user_id}:posts", 0, post_id)
        r.hincrby(f"social:user:{user_id}", "post_count", -1)

    # Remove from indexes
    if platform:
        r.srem(f"platform:{platform}:posts", post_id)
    if country:
        r.srem(f"country:{country}:posts", post_id)
    if sentiment:
        r.srem(f"sentiment:{sentiment}:posts", post_id)

    # Remove from hashtag indexes
    hashtags = get_post_hashtags(post_id)
    for tag in hashtags:
        r.srem(f"hashtag:{tag}:posts", post_id)
        r.zincrby("hashtag:trending", -1, tag)

    # Remove from trending and main index
    r.zrem("post:trending", post_id)
    r.srem("post:all", post_id)

    # Delete post data
    r.delete(f"post:{post_id}")
    r.delete(f"post:{post_id}:hashtags")

    print(f"Post {post_id} deleted.")


#############################################################
# ANALYTICAL QUERIES
#############################################################

def trending_hashtags(n=10):
    """Get top trending hashtags."""
    print(f"\nTop {n} trending hashtags:")
    results = r.zrevrange("hashtag:trending", 0, n-1, withscores=True)
    for tag, count in results:
        print(f"  #{tag.decode()}: {int(count)} posts")
    return results


def trending_posts(n=10):
    """Get top trending posts by engagement."""
    print(f"\nTop {n} trending posts:")
    results = r.zrevrange("post:trending", 0, n-1, withscores=True)
    for post_id, engagement in results:
        post = get_post(post_id.decode())
        text = post.get("text", "")[:50] + "..." if len(post.get("text", "")) > 50 else post.get("text", "")
        print(f"  [{int(engagement)} engagement] {text}")
    return results


def get_post_count():
    """Get total number of posts."""
    return r.scard("post:all")


def get_user_count():
    """Get total number of users."""
    return r.scard("social:user:all")


def platform_stats():
    """Get post count per platform."""
    print("\nPosts per platform:")
    platforms = ["twitter", "instagram", "facebook"]
    for platform in platforms:
        count = r.scard(f"platform:{platform}:posts")
        if count > 0:
            print(f"  {platform.title()}: {count} posts")


def sentiment_stats():
    """Get post count per sentiment."""
    print("\nPosts per sentiment:")
    # Support both polarity-based (Positive/Negative/Neutral) and emotion-based sentiments
    sentiments = ["positive", "negative", "neutral", "joy", "sadness", "anger", "fear", "surprise", "love", "admiration", "excitement", "thrill", "contentment"]
    for sentiment in sentiments:
        count = r.scard(f"sentiment:{sentiment}:posts")
        if count > 0:
            print(f"  {sentiment.title()}: {count} posts")


def country_stats(limit=10):
    """Get post count per country (top N)."""
    print(f"\nTop {limit} countries by post count:")
    # This requires scanning, but we can check common countries
    countries = ["usa", "uk", "germany", "france", "brazil", "india", "japan", "australia", "canada", "spain"]
    stats = []
    for country in countries:
        count = r.scard(f"country:{country}:posts")
        if count > 0:
            stats.append((country, count))

    stats.sort(key=lambda x: -x[1])
    for country, count in stats[:limit]:
        print(f"  {country.upper()}: {count} posts")


def sentiment_by_platform(platform):
    """Get sentiment distribution for a specific platform."""
    print(f"\nSentiment distribution for {platform}:")
    platform_posts = r.smembers(f"platform:{platform.lower()}:posts")

    sentiment_counts = {}
    for post_id in platform_posts:
        sentiment = r.hget(f"post:{post_id.decode()}", "sentiment")
        if sentiment:
            s = sentiment.decode()
            sentiment_counts[s] = sentiment_counts.get(s, 0) + 1

    for sentiment, count in sorted(sentiment_counts.items(), key=lambda x: -x[1]):
        print(f"  {sentiment.title()}: {count}")


def search_hashtag(hashtag):
    """Search for posts with a specific hashtag and show stats."""
    posts = r.smembers(f"hashtag:{hashtag.lower()}:posts")
    print(f"\nHashtag #{hashtag}: {len(posts)} posts")

    if posts:
        # Show some sample posts
        print("Sample posts:")
        for post_id in list(posts)[:3]:
            post = get_post(post_id.decode())
            text = post.get("text", "")[:60]
            print(f"  - {text}...")

    return list(posts)


def engagement_analysis(post_id):
    """Analyze engagement metrics for a post."""
    post = get_post(post_id)
    if not post:
        print(f"Post {post_id} not found.")
        return

    print(f"\nEngagement Analysis for Post {post_id}:")
    print(f"  Likes: {post.get('likes', 0)}")
    print(f"  Retweets: {post.get('retweets', 0)}")
    print(f"  Total Engagement: {post.get('engagement', 0)}")
    print(f"  Platform: {post.get('platform', 'N/A')}")
    print(f"  Sentiment: {post.get('sentiment', 'N/A')}")

    # Get ranking
    rank = r.zrevrank("post:trending", post_id)
    if rank is not None:
        print(f"  Trending Rank: #{rank + 1}")


#############################################################

if __name__ == "__main__":
    print("=" * 50)
    print("Social Media Use Case - Queries Demo")
    print("=" * 50)

    # Statistics
    post_count = get_post_count()
    user_count = get_user_count()
    print(f"\nTotal posts: {post_count}")
    print(f"Total users: {user_count}")

    # Platform and sentiment stats
    platform_stats()
    sentiment_stats()
    country_stats(5)

    # Trending content
    trending_hashtags(5)
    trending_posts(5)

    # Example: Specific post info
    print("\n" + "-" * 50)
    print("Example: Post Details (ID: 1)")
    print("-" * 50)

    post = get_post("1")
    if post:
        print(f"Text: {post.get('text', 'N/A')[:100]}...")
        print(f"Platform: {post.get('platform', 'N/A')}")
        print(f"Sentiment: {post.get('sentiment', 'N/A')}")
        print(f"Likes: {post.get('likes', 0)}")
        print(f"Hashtags: {get_post_hashtags('1')}")

    # Search hashtag
    search_hashtag("travel")

    # Engagement analysis
    engagement_analysis("1")

    # CRUD Demo
    print("\n" + "-" * 50)
    print("CRUD Demo")
    print("-" * 50)

    # Create user
    create_user("test_user", "TestUser123")

    # Create post
    create_post(
        "99999",
        "test_user",
        "Testing Redis for social media! #redis #nosql #testing",
        platform="twitter",
        country="germany",
        sentiment="joy"
    )

    # Read
    print(f"Post 99999: {get_post('99999')}")
    print(f"Hashtags: {get_post_hashtags('99999')}")

    # Update (like and retweet)
    like_post("99999")
    like_post("99999")
    retweet_post("99999")
    print(f"After engagement: {get_post('99999')}")

    # Delete
    delete_post("99999")
    print(f"After delete: {get_post('99999')}")
