# NoSQL Course - Redis Use Cases

## Projektübersicht

Dieses Projekt implementiert **4 Use Cases** mit **Redis** als NoSQL-Datenbank im Rahmen des NoSQL-Kurses. Es demonstriert die Stärken und Grenzen von Redis für verschiedene Anwendungsszenarien.

| Use Case | Dataset | Beschreibung |
|----------|---------|--------------|
| E-Commerce | Olist Brazilian E-Commerce | Bestellungen, Kunden, Produkte, Verkäufer |
| IoT | Intel Berkeley Lab Sensors | Sensordaten, Temperatur, Luftfeuchtigkeit |
| Social Media | Sentiment Analysis Dataset | Posts, Hashtags, Likes, Trending |
| Movies | MovieLens + TMDB | Filme, Bewertungen, Cast & Crew |

---

## 1. Schnellstart

### Voraussetzungen

- Docker Desktop
- Python 3.x

### Installation & Ausführung

```bash
# 1. Python-Dependencies installieren
# Windows:
pip install -r requirements.txt
# Mac:
pip3 install -r requirements.txt

# 2. Redis starten (Vorher Docker Desktop starten)
docker compose up -d

# 3. Hauptmenü starten
# Windows:
python main.py
# Mac:
python3 main.py
```

Das interaktive Menü bietet:
- Import der Daten für jeden Use Case
- Ausführen von Queries und CRUD-Operationen
- Vergleich aller Use Cases
- Performance-Benchmark

---

## 2. Data Model Design

Redis verwendet keine Schemas wie relationale Datenbanken. Stattdessen werden Daten in **Key-Value-Strukturen** mit verschiedenen Datentypen organisiert.

### 2.1 Verwendete Redis-Datenstrukturen

| Datentyp | Verwendung | Beispiel |
|----------|------------|----------|
| **Hash** | Entitäten mit Attributen | `post:1` -> {text, likes, sentiment} |
| **Set** | Mengen, Indexe | `hashtag:travel:posts` -> {1, 5, 23} |
| **Sorted Set** | Rankings, Time-Series | `post:trending` -> {post_id: score} |
| **List** | Chronologische Daten | `user:1:posts` -> [newest, ..., oldest] |
| **String** | Lookups, Counter | `imdb:tt0114709` -> "862" |

### 2.2 Datenmodell pro Use Case

#### E-Commerce
```
order:<id>              -> HASH (order_id, customer_id, status, total, ...)
customer:<id>           -> HASH (customer_id, city, state, ...)
customer:<id>:orders    -> LIST [order_ids...]
product:<id>            -> HASH (product_id, category, price, ...)
seller:<id>             -> HASH (seller_id, city, state, ...)
```

#### IoT
```
sensor:<id>             -> HASH (sensor_id, location, type, ...)
sensor:<id>:readings    -> SORTED SET {json_reading: timestamp}
sensor:avg:temperature  -> SORTED SET {sensor_id: avg_temp}
sensor:alerts           -> LIST [alert_messages...]
```

#### Social Media
```
post:<id>               -> HASH (text, timestamp, platform, likes, sentiment, ...)
post:<id>:hashtags      -> SET {hashtag1, hashtag2, ...}
hashtag:<tag>:posts     -> SET {post_ids...}
hashtag:trending        -> SORTED SET {hashtag: count}
post:trending           -> SORTED SET {post_id: engagement_score}
platform:<name>:posts   -> SET {post_ids...}
sentiment:<type>:posts  -> SET {post_ids...}
```

#### Movies
```
movie:<id>              -> HASH (title, release_date, budget, rating, ...)
movie:<id>:genres       -> SET {genre1, genre2, ...}
movie:<id>:cast         -> LIST [actor1, actor2, ...]
user:<id>:ratings       -> SORTED SET {movie_id: rating}
movie:top_rated         -> SORTED SET {movie_id: avg_rating}
genre:<name>:movies     -> SET {movie_ids...}
imdb:<imdb_id>          -> STRING movie_id
```

### 2.3 Design-Pattern: Multi-Index

Redis hat keine sekundären Indizes. Daher werden **manuelle Indizes** als Sets erstellt:

```python
# Ein Post wird in mehreren Indizes gespeichert
r.sadd("platform:twitter:posts", post_id)    # Index nach Plattform
r.sadd("sentiment:joy:posts", post_id)       # Index nach Sentiment
r.sadd("hashtag:travel:posts", post_id)      # Index nach Hashtag
r.sadd("country:germany:posts", post_id)     # Index nach Land
```

**Vorteil:** O(1) Lookups für jede Dimension
**Nachteil:** Redundanz, manuelle Pflege bei Updates/Deletes

---

## 3. Data Import

Jeder Use Case hat ein `import.py` Skript, das die CSV-Daten in Redis importiert.

### Import-Optimierung: Pipelining

```python
# Ohne Pipeline: 1000 Netzwerk-Roundtrips
for item in items:
    r.hset(f"key:{item.id}", mapping=item.data)

# Mit Pipeline: 1 Netzwerk-Roundtrip für 1000 Operationen
pipe = r.pipeline()
for item in items:
    pipe.hset(f"key:{item.id}", mapping=item.data)
pipe.execute()
```

**Performance-Gewinn:** 10-100x schneller

### Import-Zeiten (gemessen)

| Use Case | Records | Import-Zeit |
|----------|---------|-------------|
| E-Commerce | ~100k Orders | ~5-10s |
| IoT | ~2.3M Readings | ~30-60s |
| Social Media | ~700 Posts | <1s |
| Movies | ~45k Movies + 26M Ratings | ~3-5min |

---

## 4. CRUD Operations & Queries

Jeder Use Case hat ein `queries.py` Skript mit Beispieloperationen.

### Create
```python
# Post erstellen
r.hset("post:1", mapping={"text": "Hello!", "likes": 0})
r.sadd("post:all", "1")
r.zincrby("hashtag:trending", 1, "redis")
```

### Read
```python
# Post abrufen
post = r.hgetall("post:1")

# Top 10 Trending Hashtags
trending = r.zrevrange("hashtag:trending", 0, 9, withscores=True)
```

### Update
```python
# Like hinzufügen (atomar!)
r.hincrby("post:1", "likes", 1)

# Engagement-Score aktualisieren
r.zadd("post:trending", {"1": new_score})
```

### Delete
```python
# Post löschen (inkl. Index-Cleanup)
r.delete("post:1")
r.srem("post:all", "1")
r.zrem("post:trending", "1")
# ... weitere Indizes bereinigen
```

### Repräsentative Queries

| Query | Redis-Befehl | Komplexität |
|-------|--------------|-------------|
| Post nach ID | `HGETALL post:1` | O(N) N=Felder |
| Trending Top 10 | `ZREVRANGE post:trending 0 9` | O(log N + M) |
| Posts mit Hashtag | `SMEMBERS hashtag:travel:posts` | O(N) |
| Sensor-Readings (Zeitbereich) | `ZRANGEBYSCORE sensor:1:readings min max` | O(log N + M) |
| Anzahl aller Posts | `SCARD post:all` | O(1) |

---

## 5. Analyse der Ergebnisse

### 5.1 Data Modeling (Schema Flexibility, Relationships)

| Aspekt | Redis-Verhalten |
|--------|-----------------|
| **Schema Flexibility** | Sehr hoch - Hashes können beliebige Felder haben, keine Migration nötig |
| **Beziehungen (1:N)** | Über Lists/Sets modelliert (`user:1:posts`) |
| **Beziehungen (N:M)** | Bidirektionale Sets (`movie:1:genres` + `genre:drama:movies`) |
| **Joins** | Nicht möglich - Application-Level Joins erforderlich |
| **Denormalisierung** | Standard-Praxis für Performance |

**Bewertung:** Redis eignet sich gut für einfache Beziehungen, wird aber bei komplexen Graphstrukturen umständlich.

### 5.2 Query Capabilities and Complexity

| Stärke | Schwäche |
|--------|----------|
| O(1) Key-Lookups | Keine Ad-hoc Queries |
| O(log N) Rankings mit Sorted Sets | Keine Volltextsuche (ohne Redis Search) |
| Atomare Operationen (INCR, ZADD) | Keine JOINs |
| Pattern-basiertes Key-Scanning | Komplexe Aggregationen nur in App-Code |

**Bewertung:** Redis ist extrem schnell für vordefinierte Zugriffsmuster, aber unflexibel für explorative Queries.

### 5.3 Performance and Scalability

#### Benchmark-Ergebnisse (gemessen mit `benchmark.py`)

| Operation | Durchschnittliche Latenz | Throughput |
|-----------|-------------------------|------------|
| GET (String) | ~0.1 ms | ~10,000 ops/sec |
| HGETALL (Hash) | ~0.1-0.3 ms | ~5,000-10,000 ops/sec |
| ZREVRANGE Top 10 | ~0.1-0.2 ms | ~8,000 ops/sec |
| SCARD (Count) | ~0.05 ms | ~20,000 ops/sec |
| Pipeline (1000 ops) | ~5-10 ms total | ~100,000 ops/sec |

#### Skalierbarkeit

| Dimension | Lösung |
|-----------|--------|
| **Vertikal** | RAM erhöhen (Redis ist In-Memory) |
| **Horizontal** | Redis Cluster (automatisches Sharding) |
| **Read-Scaling** | Master-Replica Replikation |

**Limitierung:** Daten müssen in RAM passen. Bei 26M Ratings (~500MB) funktioniert Redis gut, aber bei Terabytes wird es teuer.

### 5.4 Consistency Model and Replication

| Aspekt | Redis-Verhalten |
|--------|-----------------|
| **Konsistenzmodell** | Single-Master: Strong Consistency |
| **Replikation** | Asynchron (Master -> Replica) |
| **Failover** | Redis Sentinel oder Redis Cluster |
| **Persistenz** | RDB (Snapshots) oder AOF (Append-Only File) |
| **Transaktionen** | MULTI/EXEC (nicht ACID, kein Rollback) |

**Trade-off:** Redis priorisiert **Geschwindigkeit über Durability**. Bei Crash können die letzten Sekunden verloren gehen (konfigurierbar).

### 5.5 Ease of Development and Tooling

| Pro | Contra |
|-----|--------|
| Einfache API (`redis-py`) | Kein ORM |
| Gute Dokumentation | Key-Naming-Konventionen müssen selbst definiert werden |
| Docker-Setup trivial | Keine Schema-Validierung |
| Redis CLI für Debugging | Index-Pflege ist manuell |
| Viele Client-Libraries | Keine automatischen Migrationen |

**Bewertung:** Einfacher Einstieg, aber Disziplin bei Key-Design erforderlich.

---

## 6. Vergleich: Welcher Use Case passt am besten zu Redis?

### Ranking nach Redis-Eignung

| Rang | Use Case | Eignung | Begründung |
|------|----------|---------|------------|
| 1. | **Social Media** | Excellent | Echtzeit-Counter, Trending-Listen, einfache Beziehungen |
| 2. | **IoT** | Gut | Time-Series mit Sorted Sets, hoher Write-Throughput |
| 3. | **E-Commerce** | Mittel | Gut als Cache, aber Beziehungen umständlich |
| 4. | **Movies** | Gering | Zu viele N:M-Beziehungen, große Datenmenge |

### Detailanalyse

#### Social Media - Perfekte Passung

Redis-Features die ideal passen:
- `HINCRBY` für atomare Like/Retweet-Counter
- `ZINCRBY` für Trending-Hashtags
- `ZREVRANGE` für Top-Posts in O(log N)
- Lists für User-Feeds
- Sets für Hashtag-Indexierung

```python
# Typische Social Media Operation - perfekt für Redis
r.hincrby("post:1", "likes", 1)           # Atomar, <0.1ms
r.zincrby("hashtag:trending", 1, "redis") # Echtzeit-Ranking
```

#### IoT - Gute Passung

Vorteile:
- Sorted Sets für Time-Series Daten
- Schnelle Writes für Sensor-Streams
- Range-Queries nach Zeitstempel

Einschränkungen:
- Langzeit-Archivierung braucht viel RAM
- Aggregationen (Avg über Zeit) in App-Code

#### E-Commerce - Bedingte Passung

Geeignet für:
- Session-Management
- Warenkorb (Shopping Cart)
- Produkt-Cache
- Inventory-Counter

Nicht geeignet für:
- Order-Customer-Product Beziehungen (besser: Relational DB)
- Komplexe Reports (Umsatz pro Monat, Region)

#### Movies - Weniger geeignet

Probleme:
- Viele N:M-Beziehungen (Movies - Actors - Directors - Genres)
- 26 Mio. Ratings = hoher RAM-Verbrauch
- Empfehlungsalgorithmen brauchen komplexe Queries
- Keine Volltextsuche in Titeln/Beschreibungen

Besser geeignet: MongoDB (Document), Neo4j (Graph für Empfehlungen)

---

## 7. Trade-offs und Limitierungen

### Redis Stärken

| Stärke | Erklärung |
|--------|-----------|
| **Extrem schnell** | In-Memory, Single-Threaded = keine Locks |
| **Einfache Datenstrukturen** | Hash, Set, List, Sorted Set decken 90% der Fälle ab |
| **Atomare Operationen** | INCR, ZADD, etc. sind thread-safe |
| **Pub/Sub** | Echtzeit-Events möglich |
| **TTL Support** | Automatisches Expire für Caching |

### Redis Schwächen

| Schwäche | Erklärung |
|----------|-----------|
| **RAM-limitiert** | Alle Daten müssen in Speicher passen |
| **Keine JOINs** | Beziehungen müssen in App-Code aufgelöst werden |
| **Keine Ad-hoc Queries** | Zugriffsmuster müssen vorher bekannt sein |
| **Keine Volltextsuche** | Nur mit Redis Search Modul |
| **Manuelle Indexierung** | Sekundärindizes müssen selbst gepflegt werden |

### Wann Redis verwenden?

**Ja:**
- Caching
- Sessions
- Leaderboards / Rankings
- Echtzeit-Counter
- Rate Limiting
- Message Queues
- Pub/Sub

**Nein:**
- Primary Database für komplexe Domains
- Große Datenmengen (>RAM)
- Komplexe Relationen / Graphen
- Ad-hoc Analytics
- Volltextsuche

---

## 8. Lessons Learned & Best Practices

### Key-Naming Konvention

```
<entity>:<id>                    # Hauptentität
<entity>:<id>:<attribute>        # Unter-Collection
<attribute>:<value>:<entities>   # Reverse-Index
```

Beispiele:
```
post:123                         # Post-Daten
post:123:hashtags                # Hashtags des Posts
hashtag:travel:posts             # Alle Posts mit #travel
```

### Pipeline für Bulk-Operations

```python
# IMMER Pipeline für >10 Operationen
pipe = r.pipeline()
for item in items:
    pipe.hset(...)
pipe.execute()
```

### Atomare Updates

```python
# SCHLECHT: Race Condition möglich
likes = int(r.hget("post:1", "likes"))
r.hset("post:1", "likes", likes + 1)

# GUT: Atomar
r.hincrby("post:1", "likes", 1)
```

### Index-Cleanup bei Delete

```python
def delete_post(post_id):
    post = r.hgetall(f"post:{post_id}")

    # Alle Indizes bereinigen!
    r.srem(f"platform:{post['platform']}:posts", post_id)
    r.srem(f"sentiment:{post['sentiment']}:posts", post_id)
    for tag in r.smembers(f"post:{post_id}:hashtags"):
        r.srem(f"hashtag:{tag}:posts", post_id)

    # Dann erst löschen
    r.delete(f"post:{post_id}")
    r.srem("post:all", post_id)
```

### Namespace-Prefixe für Multi-Use-Case

```python
# Vermeidet Key-Kollisionen
"social:user:1"   # Social Media User
"user:1"          # Movies User
```

---

## 9. Projektstruktur

```
nosql-course-redis/
├── main.py                 # Interaktives Hauptmenü
├── benchmark.py            # Performance-Benchmark
├── docker-compose.yml      # Redis Container
├── requirements.txt        # Python Dependencies
│
├── e_commerce/
│   ├── import.py          # Daten-Import
│   ├── queries.py         # CRUD & Queries
│   ├── data/              # CSV-Dateien
│   └── README.md          # Use Case Dokumentation
│
├── iot/
│   ├── import.py
│   ├── queries.py
│   ├── data/
│   └── README.md
│
├── social_media/
│   ├── import.py
│   ├── queries.py
│   ├── data/
│   └── README.md
│
└── movies/
    ├── import.py
    ├── queries.py
    ├── data/
    └── README.md
```

---

## 10. Fazit

### Kernaussage

> **Redis ist ein hervorragender Key-Value Store für spezifische Anwendungsfälle wie Caching, Echtzeit-Counter und Rankings. Für komplexe Datenmodelle mit vielen Beziehungen oder großen Datenmengen sind andere NoSQL-Typen (Document, Graph) besser geeignet.**

### Use Case Empfehlung

| Use Case | Empfohlene DB | Begründung |
|----------|---------------|------------|
| Social Media | **Redis** | Perfekte Passung |
| IoT | Redis oder **TimescaleDB** | Redis gut, spezialisierte Time-Series DB besser |
| E-Commerce | **PostgreSQL** + Redis Cache | Relationen wichtig |
| Movies | **MongoDB** oder **Neo4j** | Flexible Schemas / Graph-Queries |

---

## Quellen & Datasets

- [Olist Brazilian E-Commerce Dataset](https://www.kaggle.com/olistbr/brazilian-ecommerce)
- [Intel Berkeley Lab Sensor Data](http://db.csail.mit.edu/labdata/labdata.html)
- [Social Media Sentiment Dataset](https://github.com/Rajbharaman/Social-Media-Sentiment-Data-Analysis)
- [The Movies Dataset (MovieLens + TMDB)](https://www.kaggle.com/rounakbanik/the-movies-dataset)
- [Redis Documentation](https://redis.io/docs/)

---

*NoSQL Course - Hochschule Hannover - Prof. Dr. Suat Can*
