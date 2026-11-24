# Changelog

## 0.1.0-alpha.5

- Initialisierungsfehler der Start-/Stopp-Tasten behoben: interne Zielvariable
  kollidierte mit Home Assistants schreibgeschützter Eigenschaft `enabled`.
- Regressionstests für Tastenerstellung, Verfügbarkeit und Befehlsweitergabe.

## 0.1.0-alpha.4

- Start-/Stopp-Tasten aus vollständigen App-Mitschnitten ergänzt.
- Zustandsanzeige Aus / Startet / Heizbetrieb / Kühlt ab / Unbekannter Zustand.
- Start während Abkühlung gesperrt; Befehle mit aktueller Zustandsprüfung.
- Kein automatisches Wiederholen von Start-/Stopp-Schreibbefehlen.
- Befehlsannahme von vollständigem Start/Nachlauf getrennt.
- Neue Regressionstests mit aufgezeichneten Zustandsfolgen.
- Schreiben aller Stufen 1–10 samt Sprüngen inzwischen live bestätigt.
- Start/Stopp aus Home Assistant noch nicht live geprüft.

## 0.1.0-alpha.3

- Leistungsregler von 3–4 auf 1–10 erweitert, bestehende Entitätskennung erhalten.
- Zusätzliche Befehle aus bestätigtem Paketformat und Prüfsumme abgeleitet.
- Rückmeldeprüfung und einmaliges Schreiben bleiben erhalten.
- Schreiben 3 → 4 → 3 über Home Assistant/ATOM live bestätigt.
- Zusätzliche Schreibstufen stehen zum Live-Test bereit.

## 0.1.0-alpha.2

- Testregler für die exakt aufgezeichneten Stufenbefehle 3 und 4.
- Vorabprüfung von laufendem Leistungsstufenbetrieb und Rückmeldeprüfung.
- Keine automatische Wiederholung von Schreibbefehlen.
- Statusanzeige aller zehn Stufen über ATOM-Proxy live bestätigt.
- Installation über Marketplace und Änderungen per Funkfernbedienung bestätigt.
- Schreibfunktion in Home Assistant noch nicht live geprüft.

## 0.1.0-alpha.1

- Erste experimentelle Home-Assistant-Integration für BD39/BDF8.
- Bluetooth-Erkennung, manuelle Adresskonfiguration und Statussensoren.
- Initialisierung und Statusabfrage aus realen Gerätemitschnitten.
- Begrenzte Wartezeiten, Wiederverbindungsgrundlage und redigierte Diagnose.
- Deutsche/englische Oberfläche und Protokollnotizen.
- Offline-Regressionstests für Paketverarbeitung und BLE-Transport.

Noch kein Live-Test der Integration in Home Assistant oder über ESPHome-Proxy.
Schreibende Heizungssteuerung ist in dieser Alpha nicht enthalten.
