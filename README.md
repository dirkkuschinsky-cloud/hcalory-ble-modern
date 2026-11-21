# Hcalory BLE Modern

Lokale Home-Assistant-Anbindung für neuere Hcalory-Dieselheizungssteuerungen
mit dem Bluetooth-Dienst **BD39**.

**Status: experimentelle Alpha, zunächst nur Statusanzeige.**
Die Kommunikation wurde an einer Steuerung mit zehn Leistungsstufen und
dem Gerätenamen `Heater5069` untersucht. Die Integration selbst wurde noch
nicht auf einem laufenden Home Assistant oder ESPHome-Proxy getestet.

## Was bereits funktioniert

- Erkennung über BD39 und Herstellerkennung `0x0110`.
- Initialisierung, Statusabfrage und Auswertung vollständiger Antwortpakete.
- Leistungsstufe als Sensor; Betriebsart und Zustand als Diagnose-Rohwerte.
- Vorbereitung für lokale BLE-Adapter und aktive ESPHome-Bluetooth-Proxys
  über die Bluetooth-Verwaltung von Home Assistant.
- Deutsche und englische Oberfläche.

Am Acer mit Intel AX211 wurde eine durchgehende Verbindung mit 30 erfolgreichen
Statusabfragen in 30 Sekunden getestet. Die Anzeige von Stufe 3 ist bestätigt;
zusätzliche App-Mitschnitte bestätigen den Wechsel 3 → 4 → 3.

**Noch nicht enthalten:** Start/Stopp, schreibbarer Stufenregler,
Thermostat, Lüfterbetrieb, Temperatur-, Spannungs- und Höhenanzeige.
Die übrigen Leistungsstufen sind noch nicht einzeln geprüft.

## Voraussetzungen

- Zielversion: Home Assistant Core **2026.10.4 oder neuer**. Dies ist ein
  Entwicklungsziel, noch keine bestätigte Kompatibilitätszusage.
- Eine Steuerung, die den Dienst `0000bd39-0000-1000-8000-00805f9b34fb`
  und den Kanal `0000bdf8-0000-1000-8000-00805f9b34fb` anbietet.
- BLE-fähiger Adapter oder aktiver ESPHome-Bluetooth-Proxy in Reichweite.

Für Proxmox ist beispielsweise ein M5Stack ATOM Lite C008 mit
[ESPHome-Proxy-Firmware](https://esphome.io/projects/) vorgesehen.
Er benötigt WLAN und USB-Strom; USB-Passthrough entfällt.
Die ursprüngliche Hcalory-W1-Integration mit FFF0/FFF1/FFF2 wird nicht ersetzt.

## Installation für erste Tests

### Manuell

1. Den Ordner `custom_components/hcalory_ble_modern` aus diesem Projekt nach
   `/config/custom_components/hcalory_ble_modern` kopieren.
2. Home Assistant neu starten.
3. Die Handy-App und andere Verbindungen zur Heizung schließen.
4. Die entdeckte Integration hinzufügen oder unter **Einstellungen → Geräte &
   Dienste → Integration hinzufügen → Hcalory BLE Modern** die Bluetooth-Adresse
   der eigenen Heizung eintragen.

Die erste Einrichtung kann wegen der Bluetooth-Diensterkennung länger dauern.
Bei fehlender Verbindung versucht Home Assistant die Einrichtung erneut.
Im Thermostatmodus wird die Leistungsstufe als unbekannt angezeigt.

### HACS

Nach Veröffentlichung kann dieses Repository in HACS als benutzerdefiniertes
Repository vom Typ **Integration** hinzugefügt werden. `hacs.json` ist vorbereitet.
Das Projekt ist noch nicht im offiziellen HACS-Verzeichnis gelistet und eine
HACS-Installation wurde noch nicht praktisch getestet.

## Entwicklung und Nachweise

```sh
python -m unittest discover -s tests -v
python -m compileall -q custom_components
```

Die Protokolltests laufen ohne zusätzliche Pakete. Transporttests simulieren
die Bluetooth-Gegenstelle. Für Integrations-/Gerätetests ist ein separates
Home-Assistant-Testsystem erforderlich.

Die [Protokollnotizen](docs/protocol.md) trennen beobachtete Daten von Vermutungen.
Rohmitschnitte und Android-Fehlerberichte werden nicht veröffentlicht.
Testdaten enthalten nur ausgewählte Protokollframes ohne Geräteadressen oder
Zeitstempel.

## Nächste Schritte

- [ ] Statusanzeige in Home Assistant mit ATOM Lite testen.
- [ ] Wiederverbindung und längeren Betrieb mit Proxy testen.
- [ ] Stufen 1–10 prüfen und erst danach Steuerung freigeben.
- [ ] Start, Stopp und Abkühlzustände gezielt aufzeichnen.
- [ ] Temperaturen, Spannung und weitere Felder mit App-Werten abgleichen.

## Hintergrund und Lizenz

Die Untersuchung wurde durch [evanfoster/hcalory-ble](https://github.com/evanfoster/hcalory-ble)
und [evanfoster/hcalory-control](https://github.com/evanfoster/hcalory-control)
angeregt. Das erste Projekt verwendet MIT, die Bibliothek LGPL-3.0.
Dieses Projekt enthält eine eigenständige Implementierung auf Grundlage der
bereitgestellten Gerätemitschnitte; es importiert oder kopiert die Bibliothek nicht.
Es ist ein neues Projekt und kein GitHub-Fork mit übernommener Historie.

Lizenz: [MIT](LICENSE). Keine Verbindung zum Hersteller Hcalory.
