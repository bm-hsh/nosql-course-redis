# IoT Use Case

## 1. Übersicht

Dieser Ordner enthält die Implementierung des IoT-Use-Cases mit Redis als NoSQL-Datenbank. Der Use Case basiert auf dem Intel Berkeley Lab Sensor Dataset und demonstriert:

- ein Redis-Datenmodell (Hash, Sorted Set, List, Set)
- den Import von Zeitreihendaten nach Redis
- CRUD-Operationen (Create, Read, Update, Delete)
- repräsentative Queries (z. B. Zeitreihenabfragen, Temperatur-Ranking, Alerts)

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

Die Datendatei `data.txt` muss im Ordner `iot/data` liegen. Falls keine Daten vorhanden sind, generiert das Import-Skript automatisch Beispieldaten.

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

Das Skript `import.py` liest die Sensordaten ein und speichert die relevanten Informationen in Redis.

Ausführen:

```bash
cd iot
# Windows:
python import.py
# Mac:
python3 import.py
```

Erwartete Ausgabe:

```
==================================================
IoT Use Case - Data Import
==================================================

Step 1: Initializing sensors...
Initializing sensor metadata...
  -> 54 sensors initialized.

Step 2: Importing readings...
Generating sample sensor data...
  -> 54000 sample readings generated.

Step 3: Importing connectivity...
Connectivity data not found, skipping...

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

- Alle Sensor-IDs:

```
SMEMBERS sensor:all
```

- Sensor-Metadaten abrufen:

```
HGETALL sensor:1
```

- Letzte Messung eines Sensors:

```
HGETALL sensor:1:latest
```

- Top-Sensoren nach Durchschnittstemperatur:

```
ZREVRANGE sensor:avg:temperature 0 9 WITHSCORES
```

- Anzahl der Messungen eines Sensors:

```
ZCARD sensor:1:readings
```

- Zeitreihen-Abfrage (letzte 10 Messungen):

```
ZREVRANGE sensor:1:readings 0 9
```

- Aktuelle Alerts anzeigen:

```
LRANGE sensor:alerts 0 9
```

## 6. Queries und CRUD-Operationen ausführen

Das Skript `queries.py` demonstriert:

- Anlegen eines neuen Sensors (Create)
- Hinzufügen einer Messung (Create)
- Auslesen von Sensor-Metadaten (Read)
- Auslesen der letzten Messung (Read)
- Zeitreihenabfragen (Read)
- Ändern des Sensor-Status (Update)
- Löschen eines Sensors (Delete)
- Analytische Queries (Top-Sensoren, Alerts, Temperaturbereich)

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

| Zweck                          |                Redis-Key | Datentyp   |
| ------------------------------ | -----------------------: | ---------- |
| Sensor-Metadaten               |          `sensor:<id>`   | Hash       |
| Zeitreihen-Messungen           | `sensor:<id>:readings`   | Sorted Set |
| Letzte Messung                 |    `sensor:<id>:latest`  | Hash       |
| Alle Sensor-IDs                |           `sensor:all`   | Set        |
| Temperatur-Ranking             | `sensor:avg:temperature` | Sorted Set |
| Konnektivität zu anderen Sens. | `sensor:<id>:connectivity` | Hash     |
| Warnmeldungen                  |        `sensor:alerts`   | List       |

### Datenmodell-Details

**sensor:\<id\>** (Hash):
- `mote_id`: Sensor-ID
- `pos_x`, `pos_y`: Position im Labor
- `status`: active, inactive, maintenance
- `type`: Sensortyp (z.B. Mica2)

**sensor:\<id\>:readings** (Sorted Set):
- Score: Unix-Timestamp (Epoch)
- Member: JSON-String mit Messdaten (temp, humidity, light, voltage, date, time)

**sensor:\<id\>:latest** (Hash):
- `temperature`, `humidity`, `light`, `voltage`: Aktuelle Werte
- `timestamp`, `date`, `time`: Zeitstempel der Messung

**sensor:avg:temperature** (Sorted Set):
- Member: Sensor-ID
- Score: Durchschnittstemperatur

## 8. Ablaufübersicht

1. Docker starten:

```bash
docker compose up -d
```

2. Sicherstellen, dass die Datendatei `data.txt` im Ordner `iot/data` liegt (optional - sonst werden Beispieldaten generiert)

3. Daten importieren:

```bash
# Windows:
python iot/import.py
# Mac:
python3 iot/import.py
```

4. Import optional über `redis-cli` prüfen

5. Queries und CRUD demonstrieren:

```bash
# Windows:
python iot/queries.py
# Mac:
python3 iot/queries.py
```

## 9. Besonderheiten des IoT Use Cases mit Redis

### Zeitreihen-Modellierung

Redis hat kein natives Zeitreihen-Modul (ohne RedisTimeSeries-Extension), daher verwenden wir **Sorted Sets**:
- Der **Score** ist der Unix-Timestamp
- Das **Member** ist ein JSON-String mit allen Messwerten
- Zeitreihenabfragen nutzen `ZRANGEBYSCORE` für effiziente Bereichsabfragen

### Vorteile von Redis für IoT

- **Extrem schnelle Schreiboperationen**: Ideal für hochfrequente Sensordaten (31-Sekunden-Intervalle)
- **Einfache Aggregationen**: Sorted Sets ermöglichen Rankings (z.B. heißeste Sensoren)
- **TTL-Support**: Alte Daten können automatisch gelöscht werden
- **Pub/Sub**: Für Echtzeit-Alerts und Event-Streaming geeignet

### Einschränkungen

- **Speicherverbrauch**: Alle Daten im RAM, bei 2.3 Mio. Messungen relevant
- **Keine komplexen Aggregationen**: AVG, SUM etc. müssen in der Anwendung berechnet werden
- **Keine native Zeitreihen-Kompression**: Im Gegensatz zu spezialisierten Time-Series-DBs
