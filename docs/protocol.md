# Beobachtetes BD39-Protokoll

## Gegenstelle

Untersucht wurde eine Hcalory-Steuerung mit zehn Leistungsstufen. BD39 bzw.
die Herstellerkennung allein beweisen keine vollständige Modellkompatibilität.

| Eigenschaft | Beobachtung |
| --- | --- |
| Advertising-Service | `0000bd39-0000-1000-8000-00805f9b34fb` |
| Manufacturer ID | `0x0110` |
| BDF7 | write, write-without-response; in der untersuchten Sitzung nicht benutzt |
| BDF8 | read, write, write-without-response, notify |

## Erfolgreich getesteter Statusablauf

1. Verbinden und Benachrichtigungen an BDF8 aktivieren.
2. Initialisierung ohne Schreibbestätigung senden:
   `000200010001000a0c000005010000000012`
3. Nach ca. 300 ms Statusabfrage senden:
   `000200010001000e040000090000000000000000000d`
4. Vollständigen Status abwarten; nachfolgende Abfragen nutzen dieselbe Verbindung.

Das eigenständige Testprogramm verwendete ein Sekundenintervall. Die Integration
verwendet fünf Sekunden; die Anzeige wurde inzwischen über den ATOM-Proxy live getestet.
Die App sendet weitere Zeit-/Konfigurationsnachrichten. Für den 30-Sekunden-Test
waren diese nicht erforderlich. Daraus folgt keine Garantie für Langzeitbetrieb.

## Frames

Ein Frame beginnt mit sechs Headerbytes, gefolgt von einer Big-Endian-Länge
an Offset 6–7. Die beobachtete Gesamtlänge ist `8 + Länge`.
Das letzte Byte entspricht in den vorhandenen Frames der Summe der Bytes ab
Offset 8 bis vor das letzte Byte, modulo 256.

Statusheader: `000100010001` (spontan) oder `000300010001` (Antwort).
Beobachteter Statustyp: Länge `0x0023`, Byte 8 = `0x03`, insgesamt 43 Bytes.
BLE-Benachrichtigungen können mehrere Frames enthalten. Auch fragmentierte
Daten werden abgefangen; HCI-Fragmentierung im Android-Mitschnitt wurde vor
der Protokollanalyse separat zusammengesetzt.

| Offset, nullbasiert | Bedeutung | Nachweis |
| --- | --- | --- |
| 20 | Zustands-Rohwert | Zustandsfolgen für Start, Betrieb, Abkühlen und Aus aufgezeichnet |
| 21 | Betriebsart-Rohwert | `0x02` bei Leistungsstufenbetrieb; andere Modi noch nicht live geprüft |
| 22 | Einstellung | `03 → 04 → 03` passend zur App-Bedienung |

Temperatur und Spannung werden noch nicht interpretiert. Stufenanzeige nur bei
Modus 2 und Einstellung 1–10; der Wertebereich ist eine Plausibilitätsgrenze,
die Anzeige und Steuerung aller Stufen wurden inzwischen live bestätigt.

## Absolute Leistungsstufenbefehle

| Aktion in der Hersteller-App | BDF8-Payload |
| --- | --- |
| Stufe 4 | `000200010001000607000001040c` |
| Stufe 3 | `000200010001000607000001030b` |

Die Statusantwort bestätigt beide Änderungen. Es sind absolute Sollwerte,
keine Plus-/Minus-Befehle. Das Schreiben 3 → 4 → 3 wurde am 23. November 2026
zusätzlich aus Home Assistant über den ATOM-Proxy live bestätigt.

Ab Alpha.3 werden Stufen 1–10 experimentell angeboten. Das abgeleitete Format ist
`000200010001000607000001 LL CC`, wobei `LL` die Stufe und `CC` die Summe
ab Offset 8 modulo 256 ist, hier `8 + LL`. Die generierten Pakete für 3 und 4
entsprechen exakt den Originalmitschnitten. Alle zehn Schreibstufen sowie direkte Sprünge (unter anderem 10 → 3) wurden
am 23. November 2026 live aus Home Assistant über den ATOM-Proxy bestätigt.

## Start und Stopp (App-Mitschnitte vom 24. November 2026)

BDF8-Payloads mit Schreibtyp ohne Antwort:

| Aktion | Bestätigtes Paket |
| --- | --- |
| Start | `000200010001000e040000090000000000000000020f` |
| Stopp | `000200010001000e040000090000000000000000010e` |

Beobachtete Folgen an Statusoffset 20:

- Start: `0 → 128 → 129 → 131 → 135 → 133`.
- Stopp: `133 → 68 → 69 → 67 → 65 → 0`.

Die Anlaufwerte 128/129/131/135 werden gemeinsam als **Startet** angezeigt.
Die Zwischenwerte 68/69/67/65 werden gemeinsam als **Kühlt ab** angezeigt.
Es wird keine präzisere Bedeutung einzelner Phasen behauptet. 133 ist
**Heizbetrieb**, 0 ist **Aus**. Andere Werte bleiben **Unbekannter Zustand**.

Der mitgeschnittene Start ging von Modus 0 / Einstellung 0 in Modus 2 /
Stufe 1 über. Es wird kein zusätzlicher Stufen- oder Modusbefehl beim Start
übertragen. Eine Zusage zum Verhalten nach anderen früheren Einstellungen
ist daraus nicht ableitbar.

Die Starttaste wird nur bei Zustand 0 freigegeben. Stopp zunächst nur bei 133:
Ein Abbruch der Zündung wurde nicht beobachtet. Der Client prüft vor jedem
Schreibbefehl erneut den aktuellen Status; die Oberflächenfreigabe allein
ist keine Autorisierung zum Überspringen dieser Zustandsprüfung.

Eine Bestätigung des Beginns der Start-/Abkühlfolge genügt für die Befehlsannahme.
Die vollständige Sequenz läuft weiter, und die Integration zeigt ihren aktuellen
Zustand an. Ein Verbindungsfehler darf keine automatische erneute Zündung
auslösen. Deshalb wird der Schreibbefehl nicht automatisch wiederholt.

Die Anwendungspakete der Zustandsfolgen liegen als Testfixtures ohne
Bluetooth-Adressen und Zeitstempel vor. Das sind neue Framebeispiele mit anderen
Temperaturen als die älteren Stufenfixtures; keine neuen Messwertinterpretationen.

## Datenhygiene

Keine vollständigen Android-Berichte, Bluetooth-Adressen, PINs oder
Verbindungsmetadaten in Issues hochladen. Für reproduzierbare Fehler reichen
nach Möglichkeit Anwendungspakete und die Abfolge der ausgeführten Aktionen.
