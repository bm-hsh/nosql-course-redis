# E-Commerce Use Case

## 1. Übersicht

Dieser Ordner enthält die Implementierung des E-Commerce-Use-Cases mit Redis als NoSQL-Datenbank. Der Use Case basiert auf dem Olist Brazilian E-Commerce Datensatz und demonstriert:

- ein Redis-Datenmodell (Hash, List, Set, Sorted Set)
- den Import der CSV-Daten nach Redis (Kunden, Bestellungen, Produkte, Zahlungen, Reviews, Verkäufer, Geolocation)
- CRUD-Operationen (Create, Read, Update, Delete)
- repräsentative Queries (z. B. Top-Produkte, Umsatzanalyse, Review-Statistiken, geografische Analysen)

## 2. Voraussetzungen

- Docker Desktop installiert
- Python 3 installiert

Dependencies installieren (im Projekt-Root):

```bash
pip install -r requirements.txt
```

Die CSV-Dateien müssen im Ordner `e_commerce/data` liegen.

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

Das Skript `import.py` liest die Olist-Datensätze ein und speichert die relevanten Informationen in Redis.

Ausführen:

```bash
cd e_commerce
python import.py
```

Erwartete Ausgabe:

```
==================================================
E-Commerce Use Case - Data Import
==================================================

Step 1: Importing customers...
  -> 99441 customers imported.

Step 2: Importing orders...
  -> 99441 orders imported.

Step 3: Importing products...
  -> 32951 products imported.

Step 4: Importing order items...
  -> 112650 order items imported.

Step 5: Importing payments...
  -> 103886 payments imported.

Step 6: Importing reviews...
  -> 99224 reviews imported.

Step 7: Importing sellers...
  -> 3095 sellers imported.

Step 8: Importing geolocation...
  -> 19015 geolocations imported.

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

- Alle Bestellungen eines Kunden:

```
LRANGE customer:<customer_id>:orders 0 -1
```

- Bestelldetails:

```
HGETALL order:<order_id>
```

- Top-Produkte nach Verkäufen:

```
ZREVRANGE product:sales 0 9 WITHSCORES
```

- Top-Produkte nach Umsatz:

```
ZREVRANGE product:revenue 0 9 WITHSCORES
```

- Top-Kategorien nach Umsatz:

```
ZREVRANGE category:revenue 0 9 WITHSCORES
```

- Bestellungen nach Status:

```
SCARD order:status:delivered
```

- Review eines Bestellung:

```
HGETALL order:<order_id>:review
```

- Review-Verteilung:

```
ZRANGE review:score:distribution 0 -1 WITHSCORES
```

- Kunden pro Bundesstaat:

```
SCARD state:SP:customers
```

- Verkäufer pro Bundesstaat:

```
SCARD state:SP:sellers
```

## 6. Queries und CRUD-Operationen ausführen

Das Skript `queries.py` demonstriert:

**CRUD-Operationen:**
- Anlegen einer neuen Bestellung (Create)
- Anlegen eines Reviews (Create)
- Auslesen einer Bestellung (Read)
- Auslesen von Kunden, Produkten, Reviews (Read)
- Ändern des Bestellstatus (Update)
- Löschen einer Bestellung inkl. aller verknüpften Daten (Delete)

**Produktanalysen:**
- Top-Produkte nach Verkaufszahlen
- Top-Produkte nach Umsatz
- Top-Kategorien nach Umsatz

**Bestellanalysen:**
- Bestellungen nach Status
- Gesamtanzahl Bestellungen/Kunden/Produkte/Verkäufer

**Review-Analysen:**
- Review-Score-Verteilung (mit Visualisierung)
- Durchschnittlicher Review-Score
- Best/Worst bewertete Bestellungen

**Geografische Analysen:**
- Kunden pro Bundesstaat
- Verkäufer pro Bundesstaat
- Durchschnittliche Frachtkosten pro Bundesstaat

Ausführen:

```bash
python queries.py
```

Die Ergebnisse werden im Terminal ausgegeben.

## 7. Datenmodell

Das folgende Redis-Datenmodell wird verwendet:

| Zweck                       |                     Redis-Key | Datentyp   |
| --------------------------- | ----------------------------: | ---------- |
| Kundendaten                 |             `customer:<id>`   | Hash       |
| Bestellungen eines Kunden   |    `customer:<id>:orders`     | List       |
| Bestelldaten                |                `order:<id>`   | Hash       |
| Produkte einer Bestellung   |        `order:<id>:items`     | List       |
| Zahlungen einer Bestellung  |     `order:<id>:payments`     | List       |
| Review einer Bestellung     |       `order:<id>:review`     | Hash       |
| Produktdaten                |              `product:<id>`   | Hash       |
| Verkäuferdaten              |               `seller:<id>`   | Hash       |
| Geolocation (nach PLZ)      |                 `geo:<zip>`   | Hash       |
| Alle Bestellungen           |               `order:all`     | Set        |
| Alle Kunden                 |            `customer:all`     | Set        |
| Alle Produkte               |             `product:all`     | Set        |
| Alle Verkäufer              |              `seller:all`     | Set        |
| Bestellungen nach Status    |   `order:status:<status>`     | Set        |
| Kunden nach Bundesstaat     |   `state:<state>:customers`   | Set        |
| Verkäufer nach Bundesstaat  |    `state:<state>:sellers`    | Set        |
| Produkte nach Kategorie     | `category:<name>:products`    | Set        |
| Produktverkäufe (Ranking)   |           `product:sales`     | Sorted Set |
| Produktumsatz (Ranking)     |         `product:revenue`     | Sorted Set |
| Kategorie-Umsatz (Ranking)  |        `category:revenue`     | Sorted Set |
| Review-Scores               |           `review:scores`     | Sorted Set |
| Review-Verteilung           | `review:score:distribution`   | Sorted Set |

### Datenmodell-Details

**customer:\<id\>** (Hash):
- `zip`: Postleitzahl
- `city`: Stadt
- `state`: Bundesstaat (z.B. SP, RJ)

**order:\<id\>** (Hash):
- `customer_id`: Referenz zum Kunden
- `status`: Bestellstatus (delivered, shipped, processing, etc.)
- `purchase_ts`: Kaufzeitpunkt
- `approved_ts`: Genehmigungszeitpunkt
- `delivered_carrier_ts`: Übergabe an Lieferdienst
- `delivered_customer_ts`: Lieferung an Kunden
- `estimated_delivery_ts`: Geschätzte Lieferzeit
- `freight_value`: Frachtkosten
- `seller_id`: Verkäufer-ID

**product:\<id\>** (Hash):
- `category`: Produktkategorie
- `weight`: Gewicht in Gramm
- `length`, `height`, `width`: Abmessungen in cm
- `price`: Preis

**order:\<id\>:review** (Hash):
- `score`: Bewertung (1-5 Sterne)
- `comment_title`: Titel des Kommentars
- `comment`: Kommentartext (max. 500 Zeichen)
- `creation_date`: Erstellungsdatum

**order:\<id\>:payments** (List):
- JSON-Objekte mit `type`, `installments`, `value`

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

## 9. Besonderheiten des E-Commerce Use Cases mit Redis

### Multi-Index-Muster

Jede Bestellung wird in mehreren Indexes gespeichert für schnelle Abfragen:
- Nach Status: `order:status:delivered`
- Nach Kunde: `customer:<id>:orders`
- Global: `order:all`

### Ranking mit Sorted Sets

- `product:sales`: Produkte nach Verkaufszahlen (ZINCRBY bei jedem Verkauf)
- `product:revenue`: Produkte nach Umsatz
- `category:revenue`: Kategorien nach Umsatz
- `review:scores`: Bestellungen nach Review-Score

### Vorteile von Redis für E-Commerce

- **Echtzeit-Rankings**: Top-Produkte, Top-Kategorien in O(log N)
- **Schnelle Lookups**: Bestellungen, Kunden, Produkte in O(1)
- **Atomare Counter**: ZINCRBY für Verkaufszählung
- **Flexible Indexes**: Sets für Status-basierte Abfragen
- **Zeitstempel-unabhängig**: Keine teuren JOINs nötig

### Einschränkungen

- **Keine JOINs**: Beziehungen müssen manuell traversiert werden
- **Speicherverbrauch**: Jeder Index belegt zusätzlichen RAM
- **Komplexe Aggregationen**: Durchschnitte, Summen über große Mengen müssen in der App berechnet werden
- **Keine Volltextsuche**: Produktsuche erfordert Redis Search Modul

## 10. Datensatz herunterladen

Der Olist Brazilian E-Commerce Datensatz ist verfügbar unter:
https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce

Benötigte Dateien im Ordner `e_commerce/data/`:
- `olist_customers_dataset.csv`
- `olist_orders_dataset.csv`
- `olist_products_dataset.csv`
- `olist_order_items_dataset.csv`
- `olist_order_payments_dataset.csv`
- `olist_order_reviews_dataset.csv`
- `olist_sellers_dataset.csv`
- `olist_geolocation_dataset.csv`
