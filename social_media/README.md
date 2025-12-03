# Social Media Use Case

## 1. Übersicht

Dieser Ordner enthält die Implementierung des Social-Media-Use-Cases mit Redis als NoSQL-Datenbank. Der Use Case basiert auf dem Social Media Sentiment Analysis Dataset und demonstriert:

- ein Redis-Datenmodell (Hash, List, Set, Sorted Set)
- den Import von Social-Media-Posts nach Redis
- CRUD-Operationen (Create, Read, Update, Delete)
- repräsentative Queries (z. B. Trending Hashtags, Sentiment-Analyse, Plattform-Statistiken)

## 2. Voraussetzungen

- Docker Desktop installiert
- Python 3 installiert

Dependencies installieren (im Projekt-Root):

```bash
# Windows:
pip install -r requirements.txt
# Mac:
pip3 install -r requirements.txt
```

Die CSV-Datei muss im Ordner `social_media/data` liegen.

## 3. Redis über Docker starten

Im Projekt-Root befindet sich die Datei `docker-compose.yml`, die einen Redis-Container definiert.

**Wichtig:** Docker Desktop muss gestartet sein, bevor die folgenden Befehle ausgeführt werden.

Starten des Containers:

```bash
docker compose up -d
```

Überprüfen, ob Redis läuft:

```bash
docker ps
```

Der Redis-Container sollte auf Port `6379` erreichbar sein.

## 4. Daten in Redis importieren

Das Skript `import.py` liest die Social-Media-Daten ein und speichert die relevanten Informationen in Redis.

Ausführen:

```bash
cd social_media
# Windows:
python import.py
# Mac:
python3 import.py
```

Erwartete Ausgabe:

```
==================================================
Social Media Use Case - Data Import
==================================================

Importing posts...
  -> 732 posts imported.
  -> 732 users created.
  -> 23 unique hashtags indexed.

==================================================
Import finished successfully!
==================================================
```

## 5. Überprüfen, ob der Import funktioniert hat

Redis-CLI im Container öffnen:

```bash
docker exec -it <redis-container-name> redis-cli
```

Beispiel:

```bash
docker exec -it nosql-course-redis-redis-1 redis-cli
```

Alternativ den Service-Namen verwenden:
```bash
docker compose exec redis redis-cli
```

Beispielbefehle:

- Anzahl der Schlüssel:

```
DBSIZE
```

- Alle Post-IDs:

```
SMEMBERS post:all
```

- Post-Details abrufen:

```
HGETALL post:1
```

- Hashtags eines Posts:

```
SMEMBERS post:1:hashtags
```

- Trending Hashtags:

```
ZREVRANGE hashtag:trending 0 9 WITHSCORES
```

- Trending Posts (nach Engagement):

```
ZREVRANGE post:trending 0 9 WITHSCORES
```

- Posts nach Plattform:

```
SMEMBERS platform:twitter:posts
```

- Posts nach Sentiment:

```
SMEMBERS sentiment:joy:posts
```

- Posts mit bestimmtem Hashtag:

```
SMEMBERS hashtag:travel:posts
```

## 6. Queries und CRUD-Operationen ausführen

Das Skript `queries.py` demonstriert:

- Anlegen eines neuen Posts (Create)
- Anlegen eines neuen Users (Create)
- Auslesen von Post-Details (Read)
- Suche nach Hashtags (Read)
- Liken und Retweeten (Update)
- Sentiment ändern (Update)
- Löschen eines Posts (Delete)
- Trending Hashtags und Posts
- Plattform- und Sentiment-Statistiken

Ausführen:

```bash
# Windows:
python queries.py
# Mac:
python3 queries.py
```

Die Ergebnisse werden im Terminal ausgegeben.

## 7. Datenmodell

Das folgende Redis-Datenmodell wird verwendet:

| Zweck                      |                    Redis-Key | Datentyp   |
| -------------------------- | ---------------------------: | ---------- |
| Post-Daten                 |               `post:<id>`    | Hash       |
| Hashtags eines Posts       |      `post:<id>:hashtags`    | Set        |
| User-Daten                 |        `social:user:<id>`    | Hash       |
| Posts eines Users          | `social:user:<id>:posts`     | List       |
| Posts mit Hashtag          |      `hashtag:<tag>:posts`   | Set        |
| Posts pro Plattform        |   `platform:<name>:posts`    | Set        |
| Posts pro Land             |     `country:<code>:posts`   | Set        |
| Posts pro Sentiment        | `sentiment:<type>:posts`     | Set        |
| Alle Post-IDs              |               `post:all`     | Set        |
| Alle User-IDs              |        `social:user:all`     | Set        |
| Trending Posts             |          `post:trending`     | Sorted Set |
| Trending Hashtags          |       `hashtag:trending`     | Sorted Set |

### Datenmodell-Details

**post:\<id\>** (Hash):
- `text`: Post-Inhalt
- `timestamp`: Erstellungszeitpunkt
- `platform`: twitter, instagram, facebook
- `country`: Herkunftsland
- `likes`: Anzahl Likes
- `retweets`: Anzahl Retweets/Shares
- `sentiment`: Sentiment (joy, sadness, anger, etc.)
- `user_id`: Autor
- `engagement`: Berechneter Engagement-Score

**post:trending** (Sorted Set):
- Member: Post-ID
- Score: Engagement-Score (likes + retweets * 2)

**hashtag:trending** (Sorted Set):
- Member: Hashtag (ohne #)
- Score: Anzahl der Posts mit diesem Hashtag

## 8. Ablaufübersicht

1. Docker starten:

```bash
docker compose up -d
```

2. Sicherstellen, dass die CSV-Datei im Ordner `social_media/data` liegt

3. Daten importieren:

```bash
# Windows:
python social_media/import.py
# Mac:
python3 social_media/import.py
```

4. Import optional über `redis-cli` prüfen

5. Queries und CRUD demonstrieren:

```bash
# Windows:
python social_media/queries.py
# Mac:
python3 social_media/queries.py
```

## 9. Besonderheiten des Social Media Use Cases mit Redis

### Multi-Index-Muster

Jeder Post wird in mehreren Indexes gespeichert für schnelle Abfragen:
- Nach Plattform: `platform:twitter:posts`
- Nach Land: `country:germany:posts`
- Nach Sentiment: `sentiment:joy:posts`
- Nach Hashtag: `hashtag:travel:posts`

### Engagement-Tracking

- Engagement-Score wird bei jedem Like/Retweet aktualisiert
- Sorted Set ermöglicht Echtzeit-Ranking der Trending Posts
- Keine teure Neuberechnung nötig

### Vorteile von Redis für Social Media

- **Echtzeit-Performance**: Likes, Retweets in Millisekunden verarbeitet
- **Trending-Listen**: Sorted Sets für Top-Content in O(log N)
- **Hashtag-Indexierung**: SET-basierte Suche in O(1)
- **Pub/Sub möglich**: Für Echtzeit-Feeds erweiterbar
- **Counter**: HINCRBY für atomare Like/Retweet-Zähler

### Einschränkungen

- **Volltextsuche**: Keine native Suche in Post-Texten (Redis Search Modul nötig)
- **Komplexe Aggregationen**: Sentiment-Verteilung muss in der App berechnet werden
- **Speicher**: Jeder Index belegt zusätzlichen RAM
- **Keine Joins**: Beziehungen (z.B. Follower) müssen manuell modelliert werden

## 10. Datensatz herunterladen (optional)

Für die Verwendung der echten Daten:

1. Download von https://github.com/Rajbharaman/Social-Media-Sentiment-Data-Analysis
2. Datei `sentimentdataset.csv` herunterladen
3. Datei in `social_media/data/` ablegen

**Hinweis:** Die Spaltennamen im echten Datensatz können variieren. Das Import-Skript versucht verschiedene Varianten automatisch zu erkennen.
