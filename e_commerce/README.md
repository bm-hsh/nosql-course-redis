# E-Commerce Use Case

## 1. Übersicht

Dieser Ordner enthält die Implementierung des E-Commerce-Use-Cases mit Redis als NoSQL-Datenbank. Der Use Case basiert auf dem Olist Brazilian E-Commerce Datensatz und demonstriert:

- ein Redis-Datenmodell (Hash, List, Sorted Set)
- den Import der CSV-Daten nach Redis
- CRUD-Operationen (Create, Read, Update, Delete)
- repräsentative Queries (z. B. Top-Produkte, Kundenbestellungen)

## 2. Voraussetzungen

- Docker Desktop installiert
- Python 3 installiert

Redis-Python-Client installieren:

```bash
pip install redis
```

Die CSV-Dateien müssen im Ordner `e_commerce/data` liegen.

## 3. Redis über Docker starten

Im Projekt-Root befindet sich die Datei `docker-compose.yml`, die einen Redis-Container definiert.

**Wichtig:** Stelle sicher, dass Docker Desktop gestartet ist, bevor du die folgenden Befehle ausführst.

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

Das Skript `import.py` liest die Olist-Datensätze ein und speichert die relevanten Informationen in Redis.

Ausführen:

```bash
cd e_commerce
python import.py
```

Erwartete Ausgabe:

```
Importing Customers...
Importing Orders...
Importing Products...
Importing Order Items...
Import finished successfully!
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

- Kunden-Key-Liste:

```
KEYS customer:*
```

- Inhalte eines Kunden:

```
HGETALL customer:<customer_id>
```

- Top-Produkte nach Verkäufen:

```
ZREVRANGE product:sales 0 9 WITHSCORES
```

## 6. Queries und CRUD-Operationen ausführen

Das Skript `queries.py` demonstriert:

- Anlegen einer neuen Bestellung (Create)
- Auslesen einer Bestellung (Read)
- Ändern des Bestellstatus (Update)
- Löschen einer Bestellung (Delete)
- Abrufen der Bestellungen eines Kunden
- Abrufen der Top-Produkte nach Verkaufszahlen

Ausführen:

```bash
python queries.py
```

Die Ergebnisse werden im Terminal ausgegeben.

## 7. Datenmodell

Das folgende Redis-Datenmodell wird verwendet:

| Zweck                     |              Redis-Key | Datentyp   |
| ------------------------- | ---------------------: | ---------- |
| Kunde                     |        `customer:<id>` | Hash       |
| Bestellungen eines Kunden | `customer:<id>:orders` | List       |
| Bestellung                |           `order:<id>` | Hash       |
| Produkte einer Bestellung |     `order:<id>:items` | List       |
| Produkt                   |         `product:<id>` | Hash       |
| Produktverkäufe (Ranking) |        `product:sales` | Sorted Set |

Das Modell wird vollständig durch `import.py` aufgebaut.

## 8. Ablaufübersicht

1. Docker starten:

```bash
docker compose up -d
```

2. Sicherstellen, dass die CSV-Dateien im Ordner `e_commerce/data` liegen

3. Daten importieren:

```bash
python e_commerce/import.py
```

4. Import optional über `redis-cli` prüfen

5. Queries und CRUD demonstrieren:

```bash
python e_commerce/queries.py
```