# Hcalory BLE Modern

Lokale Home-Assistant-Anbindung für neuere Hcalory-Dieselheizungssteuerungen
mit dem Bluetooth-Dienst **BD39**.

**Status: experimentelle Alpha mit Statusanzeige und Testregler für Stufen 3 und 4.**
Die Kommunikation wurde an einer Steuerung mit zehn Leistungsstufen und
dem Gerätenamen `Heater5069` untersucht. Die Statusanzeige wurde inzwischen in Home Assistant über einen M5Stack ATOM Lite
als ESPHome-Bluetooth-Proxy live getestet. Schreibende Steuerung steht zum Test bereit.

## Was bereits funktioniert

- Erkennung über BD39 und Herstellerkennung `0x0110`.
- Initialisierung, Statusabfrage und Auswertung vollständiger Antwortpakete.
- Leistungsstufe als Sensor; Betriebsart und Zustand als Diagnose-Rohwerte.
- Vorbereitung für lokale BLE-Adapter und aktive ESPHome-Bluetooth-Proxys
  über die Bluetooth-Verwaltung von Home Assistant.
- Testregler für die aufgezeichneten absoluten Stufenbefehle 3 und 4, mit Rückmeldeprüfung.
- Deutsche und englische Oberfläche.

Am Acer mit Intel AX211 wurde eine durchgehende Verbindung mit 30 erfolgreichen
Statusabfragen in 30 Sekunden getestet. Die Anzeige von Stufe 3 ist bestätigt;
zusätzliche App-Mitschnitte bestätigen den Wechsel 3 → 4 → 3.
Am 23. November 2026 wurden alle zehn Stufen über den ATOM-Proxy in Home Assistant
angezeigt. Änderungen per Funkfernbedienung werden ebenfalls übernommen; bei
einem Wechsel 1 → 2 wurde eine Verzögerung von etwa zwei Sekunden beobachtet.
Dies ist ein erster Praxistest, noch kein Langzeitnachweis.

**Noch nicht enthalten:** Start/Stopp, schreibbare Stufen 1–2 und 5–10,
Thermostat, Lüfterbetrieb, Temperatur-, Spannungs- und Höhenanzeige.
Die Anzeige aller zehn Stufen ist bestätigt; die Schreibbefehle 3 und 4 wurden
bisher nur in der Hersteller-App beobachtet.

## Voraussetzungen

- Zielversion: Home Assistant Core **2026.10.4 oder neuer**. Dies ist ein
  erste getestete Zielversion; andere Versionen sind noch nicht separat geprüft.
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
Das Projekt ist noch nicht im offiziellen Verzeichnis gelistet. Die Installation
über „Marketplace → Über Link hinzufügen“ wurde am 23. November 2026 getestet.

## Testregler in 0.1.0-alpha.2

Nach dem Update Home Assistant neu starten. Am vorhandenen Gerät erscheint
**„Leistungsstufe einstellen (Test 3–4)“**. Die bisherige Sensoranzeige bleibt erhalten.

1. Heizung am Bedienpanel auf Stufe 3 im laufenden Leistungsstufenbetrieb stellen.
2. In Home Assistant den Testregler auf 4 stellen; tatsächliche Änderung am
   Bedienpanel und am separaten Leistungssensor prüfen.
3. Danach über den Testregler auf 3 zurückstellen und erneut vergleichen.

Der Regler sendet nur die exakt mitgeschnittenen Befehle 3 und 4. Vor dem
Schreiben wird der aktuelle Zustand abgefragt. Nur bei Zustand 133 und Modus 2
wird geschrieben; Start und Moduswechsel werden nicht ausgelöst. Es gibt keine
optimistische Bestätigung. Nach dem einmaligen Schreibbefehl wird die passende
Statusantwort bis zu fünfmal angefragt. Bei fehlender Bestätigung erscheint ein
Fehler; der Befehl wird nicht automatisch erneut gesendet. Die Heizung könnte
bei einem Verbindungsfehler trotzdem bereits umgestellt haben – am Bedienpanel
prüfen. Steht die Heizung außerhalb von 3/4, bleibt der Testregler zunächst
unbekannt, während der separate Sensor weiterhin die tatsächliche Stufe zeigt.

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

- [x] Statusanzeige in Home Assistant mit ATOM Lite testen.
- [ ] Wiederverbindung und längeren Betrieb mit Proxy testen.
- [x] Anzeige aller Stufen 1–10 prüfen.
- [ ] Testregler 3 → 4 → 3 in Home Assistant prüfen; danach weitere Schreibstufen freigeben.
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
