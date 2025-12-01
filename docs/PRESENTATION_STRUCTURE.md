# Präsentations- und Report-Struktur

## Übersicht

Dieses Dokument enthält die empfohlene Struktur für:
1. **Schriftlicher Report** (12-16 Seiten)
2. **PowerPoint-Präsentation** (ca. 5 Min pro Student)

---

## 1. Report-Gliederung (12-16 Seiten)

```
1. Einleitung (1 Seite)
   1.1 Motivation und Zielsetzung
   1.2 Aufbau der Arbeit

2. Grundlagen: Redis als Key-Value Store (2-3 Seiten)
   2.1 NoSQL-Kategorien im Überblick
   2.2 Key-Value Stores: Prinzipien und Datenstrukturen
   2.3 Redis: Architektur und Besonderheiten
       - In-Memory-Konzept
       - Datentypen (String, Hash, List, Set, Sorted Set)
       - Konsistenzmodell und Replikation
       - Skalierungsstrategien (Redis Cluster)

3. Use Cases und Datensätze (1-2 Seiten)
   3.1 Übersicht der vier Use Cases
   3.2 Datensatzbeschreibung und Quellen
       - E-Commerce (Olist Brazilian Dataset)
       - IoT (Intel Berkeley Lab Sensors)
       - Social Media (Sentiment Analysis)
       - Movies (MovieLens + TMDB)

4. Datenmodellierung und Implementierung (3-4 Seiten)
   4.1 Allgemeine Modellierungsprinzipien in Redis
   4.2 Datenmodell pro Use Case
       - Key-Namenskonventionen
       - Verwendete Datentypen
       - Indexierungsstrategien
   4.3 Import-Prozess und Pipelining
   4.4 CRUD-Operationen (Beispiele)

5. Ergebnisse und Analyse (3-4 Seiten)
   5.1 Performance-Messungen (Import-Zeiten, Query-Zeiten)
   5.2 Query-Komplexität pro Use Case
   5.3 Speicherverbrauch
   5.4 Eignung der Use Cases für Redis (Ranking)
       - Social Media: Beste Eignung
       - IoT: Gute Eignung
       - E-Commerce: Mittlere Eignung
       - Movies: Eingeschränkte Eignung

6. Vergleich mit anderen NoSQL-Typen (2 Seiten)
   6.1 Redis vs. Document Store (MongoDB)
   6.2 Redis vs. Graph Database (Neo4j)
   6.3 Redis vs. Column Store (Cassandra)
   6.4 Zusammenfassung: Stärken und Schwächen

7. Fazit und Lessons Learned (1 Seite)
   7.1 Erkenntnisse zur Datenbankauswahl
   7.2 Best Practices für Redis
   7.3 Ausblick

Literaturverzeichnis

Anhang
   A. Redis-Konfiguration
   B. Datenmodell-Übersichten (Tabellen)
   C. Code-Auszüge (optional)
```

### Seitenverteilung

| Kapitel | Seiten |
|---------|--------|
| 1. Einleitung | 1 |
| 2. Grundlagen | 2-3 |
| 3. Use Cases | 1-2 |
| 4. Implementierung | 3-4 |
| 5. Ergebnisse | 3-4 |
| 6. Vergleich | 2 |
| 7. Fazit | 1 |
| **Gesamt** | **13-17** |

---

## 2. PowerPoint-Struktur (15 Folien)

Für **4 Studenten à 5 Minuten** (ca. 3-4 Folien pro Person):

### Student 1: Redis als Key-Value Store (5 min)

| Folie | Inhalt |
|-------|--------|
| 1 | **Titelfolie** - Thema, Gruppenmitglieder, Datum, "Redis - Key-Value Store" |
| 2 | **NoSQL-Kategorien im Überblick** - Document, Column, Graph, Key-Value (Redis hervorheben), Kernprinzip: Schlüssel → Wert |
| 3 | **Redis Datenstrukturen** - String, Hash, List, Set, Sorted Set mit Grafik/Diagramm |
| 4 | **Redis Architektur** - In-Memory, Single-Threaded, Replikation, Konsistenzmodell, Skalierung (Redis Cluster) |

### Student 2: Datenmodellierung (5 min)

| Folie | Inhalt |
|-------|--------|
| 5 | **Use Cases im Überblick** - E-Commerce, IoT, Social Media, Movies mit Datensatzgrößen |
| 6 | **Key-Namenskonventionen** - Schema: `entity:id:attribute`, Beispiele: `order:123`, `sensor:5:readings` |
| 7 | **Datenmodell-Diagramm** - Visualisierung eines Use Cases, Datentyp-Zuordnung |
| 8 | **Indexierungsstrategien** - Multi-Index-Pattern (Sets), Sorted Sets für Rankings |

### Student 3: Query-Beispiele (5 min)

| Folie | Inhalt |
|-------|--------|
| 9 | **CRUD-Operationen** - CREATE: HSET, SADD, ZADD / READ: HGETALL, SMEMBERS, ZRANGE / UPDATE: HINCRBY, ZINCRBY / DELETE: DEL, SREM |
| 10 | **Analytische Queries** - Code-Snippets: Top-10 Produkte, Trending Hashtags, Zeitreihen |
| 11 | **Query-Komplexität** - O(1) für Hash-Lookups, O(log N) für Sorted Sets, Tabelle mit Beispielen |

### Student 4: Analyse & Fazit (5 min)

| Folie | Inhalt |
|-------|--------|
| 12 | **Performance-Ergebnisse** - Import-Zeiten pro Use Case (Tabelle/Balkendiagramm), Query-Zeiten |
| 13 | **Eignung pro Use Case** - Ranking-Tabelle mit Begründung |
| 14 | **Redis vs. Andere Systeme** - Vergleichstabelle (MongoDB, Neo4j, Cassandra) |
| 15 | **Lessons Learned & Fazit** - Ideale Einsatzgebiete, Einschränkungen, Best Practices |

### Zusammenfassung

| Student | Fokus | Folien | Zeit |
|---------|-------|--------|------|
| 1 | Redis-Theorie (NoSQL-Typ, Architektur) | 1-4 | 5 min |
| 2 | Datenmodellierung (Schema, Patterns) | 5-8 | 5 min |
| 3 | Queries (CRUD, Analytik, Code) | 9-11 | 5 min |
| 4 | Analyse (Performance, Vergleich, Fazit) | 12-15 | 5 min |

**Total: 15 Folien für 20 Minuten**

---

## 3. Beispiel-Inhalte für Folien

### Folie 13: Eignung pro Use Case

| Use Case | Eignung | Begründung |
|----------|---------|------------|
| Social Media | ★★★★★ | Counter, Rankings, einfache Beziehungen |
| IoT | ★★★★☆ | Zeitreihen, Alerts, schnelle Writes |
| E-Commerce | ★★★☆☆ | Viele Beziehungen, komplexe Queries |
| Movies | ★★☆☆☆ | Komplexe Aggregationen, viele JOINs |

### Folie 14: Redis vs. Andere Systeme

| Kriterium | Redis | MongoDB | Neo4j |
|-----------|-------|---------|-------|
| Schema | Flexibel | Flexibel | Graph |
| Joins | Manuell | $lookup | Native |
| Performance | Sehr gut | Gut | Mittel |
| Aggregationen | Limitiert | Stark | Mittel |
| Beziehungen | Sets/Lists | Embedded/Ref | Kanten |

### Folie 15: Lessons Learned

**Redis ideal für:**
- Caching und Sessions
- Echtzeit-Rankings und Leaderboards
- Counter und Metriken
- Pub/Sub und Message Queues

**Redis weniger geeignet für:**
- Komplexe Beziehungen (→ Graph DB)
- Ad-hoc Aggregationen (→ Document DB)
- Komplexe Transaktionen (→ RDBMS)

**Best Practice:**
> Redis als Ergänzung zu RDBMS/Document Store, nicht als Ersatz

---

## 4. Orientierung an Projektanforderungen

Die Struktur deckt alle geforderten Punkte ab:

### Report-Anforderungen ✓

- [x] Title page (group members, topic, database type, date)
- [x] Description of the use case
- [x] Data modeling and implementation
- [x] Results and analysis
- [x] Comparative discussion
- [x] Conclusion and lessons learned

### Präsentations-Anforderungen ✓

- [x] Introduction of your database type and model
- [x] Demonstration of sample queries
- [x] Key findings and insights

### Analyse-Kriterien ✓

- [x] Data modeling (schema flexibility, representation of relationships)
- [x] Query capabilities and complexity
- [x] Performance and scalability
- [x] Consistency model and replication
- [x] Ease of development and tooling
