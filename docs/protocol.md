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
| 20 | Zustands-Rohwert | `0x85` bei laufender Heizung beobachtet; andere Werte ungeprüft |
| 21 | Betriebsart-Rohwert | `0x02` bei Leistungsstufenbetrieb; andere Modi noch nicht live geprüft |
| 22 | Einstellung | `03 → 04 → 03` passend zur App-Bedienung |

Temperatur und Spannung werden noch nicht interpretiert. Stufenanzeige nur bei
Modus 2 und Einstellung 1–10; der Wertebereich ist eine Plausibilitätsgrenze,
keine Bestätigung aller Stufen am Gerät.

## Beobachtete Schreibbefehle, als Testregler 3/4 freigegeben

| Aktion in der Hersteller-App | BDF8-Payload |
| --- | --- |
| Stufe 4 | `000200010001000607000001040c` |
| Stufe 3 | `000200010001000607000001030b` |

Die Statusantwort bestätigt beide Änderungen. Es sind absolute Sollwerte,
keine Plus-/Minus-Befehle. Andere Stufen lassen sich als Hypothese ableiten,
werden vor ihrer praktischen Prüfung aber nicht angeboten.
Die Anzeige aller zehn Stufen wurde am 23. November 2026 über den ATOM-Proxy
bestätigt; dies belegt noch nicht das Schreiben dieser Stufen aus Home Assistant.

## Datenhygiene

Keine vollständigen Android-Berichte, Bluetooth-Adressen, PINs oder
Verbindungsmetadaten in Issues hochladen. Für reproduzierbare Fehler reichen
nach Möglichkeit Anwendungspakete und die Abfolge der ausgeführten Aktionen.
