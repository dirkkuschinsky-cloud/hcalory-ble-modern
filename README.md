# Hcalory BLE Modern

Lokale Home-Assistant-Anbindung für neuere Hcalory-Dieselheizungssteuerungen
mit dem Bluetooth-Dienst **BD39**.

**Status: experimentelle Alpha mit Leistungsregler 1–10, Start/Stopp und Zustandsanzeige.**
Die Kommunikation wurde an einer Steuerung mit zehn Leistungsstufen und
dem Gerätenamen `Heater5069` untersucht. Die Statusanzeige wurde inzwischen in Home Assistant über einen M5Stack ATOM Lite
als ESPHome-Bluetooth-Proxy live getestet. Die Anzeige und Steuerung aller zehn Stufen sind live bestätigt,
einschließlich direkter Sprünge wie 10 → 3. Start/Stopp stehen mit Alpha.4
auf Grundlage vollständiger App-Mitschnitte zum Home-Assistant-Test bereit.

## Was bereits funktioniert

- Erkennung über BD39 und Herstellerkennung `0x0110`.
- Initialisierung, Statusabfrage und Auswertung vollständiger Antwortpakete.
- Leistungsstufe und verständlicher Heizungszustand als Sensoren; Diagnose-Rohwerte bleiben erhalten.
- Start-/Stopp-Tasten mit Rückmeldeprüfung und Startsperre während des Abkühlens.
- Vorbereitung für lokale BLE-Adapter und aktive ESPHome-Bluetooth-Proxys
  über die Bluetooth-Verwaltung von Home Assistant.
- Leistungsregler 1–10 mit Rückmeldeprüfung, auf Grundlage der bestätigten Befehle 3 und 4.
- Deutsche und englische Oberfläche.

Am Acer mit Intel AX211 wurde eine durchgehende Verbindung mit 30 erfolgreichen
Statusabfragen in 30 Sekunden getestet. Die Anzeige von Stufe 3 ist bestätigt;
zusätzliche App-Mitschnitte bestätigen den Wechsel 3 → 4 → 3.
Am 23. November 2026 wurden alle zehn Stufen über den ATOM-Proxy in Home Assistant
angezeigt. Änderungen per Funkfernbedienung werden ebenfalls übernommen; bei
einem Wechsel 1 → 2 wurde eine Verzögerung von etwa zwei Sekunden beobachtet.
Dies ist ein erster Praxistest, noch kein Langzeitnachweis.

**Noch nicht enthalten:**
Thermostat, Lüfterbetrieb, Temperatur-, Spannungs- und Höhenanzeige.
Die Leistungsregelung ist an einer Steuerung geprüft. Die neuen Start-/Stopp-Tasten
sind noch nicht live aus Home Assistant getestet.

## Voraussetzungen

- Zielversion: Home Assistant Core **2026.10.4 oder neuer**. Dies ist die
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

## Leistungsregler

Nach dem Update Home Assistant neu starten. Am vorhandenen Gerät erscheint
**„Leistungsstufe einstellen“** mit dem Bereich 1–10. Die bisherige Entität wird
weiterverwendet; eine manuell vergebene Bezeichnung kann den alten Testnamen
behalten. Der separate Sensor zeigt weiterhin die tatsächlich gemeldete Stufe.

Zum ersten Test die laufende Heizung im Leistungsstufenbetrieb belassen und
am Gerät beobachten. Stufen einzeln aus Home Assistant ändern, jeweils die
Bestätigung und tatsächliche Änderung am Bedienpanel abwarten. Beispielsweise
zunächst 3 → 2 → 1 → 3, danach bei Bedarf die höheren Stufen schrittweise testen.

Vor dem Schreiben wird der aktuelle Zustand abgefragt. Nur bei Zustand 133 und
Modus 2 wird geschrieben; Start und Moduswechsel werden nicht ausgelöst.
Es gibt keine optimistische Bestätigung. Nach dem einmaligen Schreibbefehl wird
die passende Statusantwort bis zu fünfmal angefragt. Bei fehlender Bestätigung
erscheint ein Fehler; der Befehl wird nicht automatisch erneut gesendet.
Die Heizung könnte bei einem Verbindungsfehler trotzdem bereits umgestellt
haben – am Bedienpanel prüfen.

## Start/Stopp und Zustandsanzeige ab 0.1.0-alpha.5

Alpha.5 behebt die fehlenden Start-/Stopp-Tasten der Alpha.4.
Nach dem Update Home Assistant neu starten und eine für Mitschnitte deaktivierte
Integration wieder aktivieren. Die Hersteller-App schließen, damit der Proxy
wieder verbinden kann. Am vorhandenen Gerät erscheinen:

- **Heizung starten**: nur bei bestätigtem Zustand **Aus** verfügbar.
- **Heizung stoppen**: zunächst nur bei bestätigtem **Heizbetrieb** verfügbar.
- **Heizungszustand**: **Aus**, **Startet**, **Heizbetrieb**, **Kühlt ab** oder
  **Unbekannter Zustand**.

Nach Start/Stopp wird auf die Rückmeldung gewartet, dass die zugehörige Sequenz
begonnen hat. Der Vorgang muss dafür noch nicht abgeschlossen sein. Während
**Startet** und **Kühlt ab** bleiben die Leistungsregelung und die beiden Tasten
gesperrt. Der Zustand wird über die normalen Statusabfragen weiter aktualisiert.
Ein fehlender Bluetooth-Kontakt macht die Entitäten nicht verfügbar; er bedeutet
niemals, dass die Heizung aus ist. Unbekannte Zustandswerte gelten ebenfalls
nicht als aus und geben den Startknopf nicht frei.

Ein Heizbefehl wird nur einmal gesendet und nach einem Verbindungsabbruch nicht
automatisch wiederholt. Bei unklarer Bestätigung den tatsächlichen Zustand am
Gerät prüfen. Die Tasten schalten nicht die Stromversorgung: Die Heizung führt
ihren Nachlauf selbst aus. Stopp während der Startphase ist noch nicht angeboten,
weil hierfür kein Mitschnitt vorliegt. Die normale Gerätebedienung bleibt verfügbar.

Erster Home-Assistant-Test: Im Heizbetrieb **Heizung stoppen** drücken, **Kühlt ab**
beobachten und den vollständigen Nachlauf bis **Aus** abwarten. Anschließend
**Heizung starten** drücken und **Startet → Heizbetrieb** mit dem Bedienpanel
vergleichen. Im App-Mitschnitt dauerte der Nachlauf etwa 4:48 Minuten, der Start
etwa 2:06 Minuten. Das sind beobachtete Zeiten eines Ablaufs und keine Timerwerte.

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
- [x] Testregler 3 → 4 → 3 in Home Assistant prüfen.
- [x] Alle Schreibstufen 1–10 und direkte Sprünge live prüfen.
- [x] Start, Stopp und Abkühlzustände gezielt aufzeichnen.
- [ ] Start/Stopp und Zustandsanzeige aus Home Assistant live prüfen.
- [ ] Temperaturen, Spannung und weitere Felder mit App-Werten abgleichen.

## Hintergrund und Lizenz

Die Untersuchung wurde durch [evanfoster/hcalory-ble](https://github.com/evanfoster/hcalory-ble)
und [evanfoster/hcalory-control](https://github.com/evanfoster/hcalory-control)
angeregt. Das erste Projekt verwendet MIT, die Bibliothek LGPL-3.0.
Dieses Projekt enthält eine eigenständige Implementierung auf Grundlage der
bereitgestellten Gerätemitschnitte; es importiert oder kopiert die Bibliothek nicht.
Es ist ein neues Projekt und kein GitHub-Fork mit übernommener Historie.

Lizenz: [MIT](LICENSE). Keine Verbindung zum Hersteller Hcalory.
