# Movies Use Case

## 1. Übersicht

Dieser Ordner enthält die Implementierung des Movies-Use-Cases mit Redis als NoSQL-Datenbank. Der Use Case basiert auf dem Movies Dataset (Kaggle) und demonstriert:

- ein Redis-Datenmodell (Hash, List, Set, Sorted Set)
- den Import von Film- und Bewertungsdaten nach Redis
- CRUD-Operationen (Create, Read, Update, Delete)
- repräsentative Queries (z. B. Top-Filme, Genre-Suche, Empfehlungen)

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

Die CSV-Dateien müssen im Ordner `movies/data` liegen. Falls keine Daten vorhanden sind, generiert das Import-Skript automatisch Beispieldaten.

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

Das Skript `import.py` liest die Filmdaten ein und speichert die relevanten Informationen in Redis.

Ausführen:

```bash
cd movies
# Windows:
python import.py
# Mac:
python3 import.py
```

Erwartete Ausgabe:

```
==================================================
Movies Use Case - Data Import
==================================================

Step 1: Importing movies...
  -> 45466 movies imported.

Step 2: Importing credits...
  -> 45476 credits imported.

Step 3: Importing ratings...
  -> 26024289 ratings imported.

Step 4: Importing keywords...
  -> 46419 keyword sets imported.

Step 5: Importing links...
  -> 45843 links imported.

==================================================
Import finished successfully!
==================================================
```

**Hinweis:** Der Import von 26 Mio. Ratings kann mehrere Minuten dauern. Für schnellere Tests `ratings_small.csv` verwenden.

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

- Alle Film-IDs:

```
SMEMBERS movie:all
```

- Film-Details abrufen:

```
HGETALL movie:1
```

- Genres eines Films:

```
SMEMBERS movie:1:genres
```

- Cast eines Films:

```
LRANGE movie:1:cast 0 -1
```

- Top bewertete Filme:

```
ZREVRANGE movie:top_rated 0 9 WITHSCORES
```

- Filme eines Genres:

```
SMEMBERS genre:drama:movies
```

- Bewertungen eines Users:

```
ZRANGE user:1:ratings 0 -1 WITHSCORES
```

- Film per IMDB-ID finden:

```
GET imdb:tt0114709
```

- Film per TMDB-ID finden:

```
GET tmdb:862
```

- Keywords eines Films:

```
SMEMBERS movie:1:keywords
```

## 6. Queries und CRUD-Operationen ausführen

Das Skript `queries.py` demonstriert:

- Anlegen eines neuen Films (Create)
- Hinzufügen einer Bewertung (Create)
- Watchlist-Verwaltung (Create)
- Auslesen von Filmdetails (Read)
- Auslesen von Cast & Crew (Read)
- Suche per IMDB/TMDB-ID (Read)
- Genre-basierte Suche (Read)
- Ändern von Filmdaten (Update)
- Löschen eines Films (Delete)
- Empfehlungen basierend auf Genres
- Ähnliche Filme finden

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

| Zweck                      |                   Redis-Key | Datentyp   |
| -------------------------- | --------------------------: | ---------- |
| Film-Metadaten             |             `movie:<id>`    | Hash       |
| Genres eines Films         |      `movie:<id>:genres`    | Set        |
| Cast eines Films           |        `movie:<id>:cast`    | List       |
| Crew eines Films           |        `movie:<id>:crew`    | List       |
| Bewertungen eines Films    |     `movie:<id>:ratings`    | Sorted Set |
| Keywords eines Films       |    `movie:<id>:keywords`    | Set        |
| User-Daten                 |              `user:<id>`    | Hash       |
| Bewertungen eines Users    |      `user:<id>:ratings`    | Sorted Set |
| Watchlist eines Users      |    `user:<id>:watchlist`    | Set        |
| Filme pro Genre            | `genre:<name>:movies`       | Set        |
| Filme pro Schauspieler     | `actor:<name>:movies`       | Set        |
| Filme pro Regisseur        | `director:<name>:movies`    | Set        |
| Alle Film-IDs              |             `movie:all`     | Set        |
| Alle User-IDs              |              `user:all`     | Set        |
| Top bewertete Filme        |        `movie:top_rated`    | Sorted Set |
| Beliebteste Filme          |          `movie:popular`    | Sorted Set |
| IMDB-ID Lookup             |        `imdb:<imdb_id>`     | String     |
| TMDB-ID Lookup             |        `tmdb:<tmdb_id>`     | String     |

### Datenmodell-Details

**movie:\<id\>** (Hash):
- `title`: Filmtitel
- `original_title`: Originaltitel
- `release_date`: Erscheinungsdatum
- `budget`, `revenue`: Budget und Einnahmen
- `runtime`: Laufzeit in Minuten
- `vote_average`, `vote_count`: TMDB-Bewertung
- `popularity`: Popularitätsscore
- `overview`: Kurzbeschreibung
- `language`: Originalsprache
- `imdb_id`, `tmdb_id`: Externe IDs für IMDB/TMDB
- `user_rating_avg`, `user_rating_count`: Nutzer-Bewertungen

**movie:\<id\>:ratings** (Sorted Set):
- Member: User-ID
- Score: Bewertung (1-5 Sterne)

**user:\<id\>:ratings** (Sorted Set):
- Member: Movie-ID
- Score: Bewertung (1-5 Sterne)

**movie:top_rated** (Sorted Set):
- Member: Movie-ID
- Score: Durchschnittsbewertung

## 8. Ablaufübersicht

1. Docker starten:

```bash
docker compose up -d
```

2. Sicherstellen, dass die CSV-Dateien im Ordner `movies/data` liegen (optional - sonst werden Beispieldaten generiert)

3. Daten importieren:

```bash
# Windows:
python movies/import.py
# Mac:
python3 movies/import.py
```

4. Import optional über `redis-cli` prüfen

5. Queries und CRUD demonstrieren:

```bash
# Windows:
python movies/queries.py
# Mac:
python3 movies/queries.py
```

## 9. Besonderheiten des Movies Use Cases mit Redis

### Empfehlungssystem-Muster

Redis eignet sich gut für einfache Empfehlungssysteme:
- **Genre-basiert**: Finde Filme in Genres, die der User mag
- **Ähnlichkeit**: Filme mit überlappenden Genres
- **Watchlist**: SET für schnelle Mitgliedschaftsprüfung

### Vorteile von Redis für Movies

- **Schnelle Lookups**: Filmdetails in O(1) abrufbar
- **Flexible Sets**: Genre-Indexe, Actor-Indexe ohne Schema
- **Rankings**: Sorted Sets für Top-Listen (Bewertung, Popularität)
- **Watchlists**: SETs für schnelle add/remove/check Operationen

### Einschränkungen

- **Komplexe Joins**: Keine nativen JOINs (z.B. "Alle Filme mit Actor X und Director Y")
- **Aggregationen**: AVG, COUNT etc. müssen in der Anwendung berechnet werden
- **Speicher**: 45.000 Filme + 26 Mio. Ratings benötigen viel RAM
- **Textsuche**: Keine native Volltextsuche (Redis Search Modul wäre nötig)

## 10. Kaggle-Daten herunterladen (optional)

Für die Verwendung der echten Daten:

1. Download von https://www.kaggle.com/rounakbanik/the-movies-dataset
2. Dataset herunterladen
3. Folgende Dateien nach `movies/data/` entpacken:
   - `movies_metadata.csv`
   - `credits.csv`
   - `ratings.csv` (oder `ratings_small.csv` für schnelleren Import)
   - `keywords.csv`
   - `links.csv` (oder `links_small.csv`)
