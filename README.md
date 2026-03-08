# NESO Monitor
## Aplikacja monitorowania zmian statusów stacji tankowania wodoru Neso.

Aplikacja pobiera stronę https://www.stacjeneso.pl a następnie wyszukuje tag ```<script id="stations-data">``` zawierający informacje o statusach poszczególnych stacji tankowania wodoru oraz listę komunikatów w klasie ```.section--slider__container```.

Obiekt ```stations-data``` zawiera następujące informacje:
```
[
  {
    "params": [
      51.22970573325001,
      22.627212680521577
    ],
    "status": "open",
    "statusLabel": " Stacja czynna 24/7 ",
    "customLabel": "",
    "adress": "ul. E. Plewińskiego ",
    "city": " Lublin",
    "price": " 69.00 ",
    "priceLabel": "cena: ",
    "priceUnits": "zł/kg",
    "navLabel": "Nawiguj",
    "coordLabel": "Kopiuj współrzędne"
  },
  {
    "params": [
      54.32432539890899,
      18.54680655521346
    ],
    "status": "open",
    "statusLabel": " Stacja czynna 24/7 ",
    "customLabel": "",
    "adress": "ul. Jabłoniowa ",
    "city": " Gdańsk",
    "price": " 69.00 ",
    "priceLabel": "cena: ",
    "priceUnits": "zł/kg",
    "navLabel": "Nawiguj",
    "coordLabel": "Kopiuj współrzędne"
  },
  {
    "params": [
      54.45603037181641,
      18.453483064666404
    ],
    "status": "open",
    "statusLabel": " Stacja czynna 24/7 ",
    "customLabel": "",
    "adress": "ul. Starochwaszczyńska ",
    "city": " Gdynia",
    "price": " 69.00 ",
    "priceLabel": "cena: ",
    "priceUnits": "zł/kg",
    "navLabel": "Nawiguj",
    "coordLabel": "Kopiuj współrzędne"
  },
  {
    "params": [
      50.10173454074803,
      18.532959765193265
    ],
    "status": "open",
    "statusLabel": " Stacja czynna 24/7 ",
    "customLabel": "",
    "adress": "ul. Budowlanych 6",
    "city": "44-200 Rybnik",
    "price": " 69.00 ",
    "priceLabel": "cena: ",
    "priceUnits": "zł/kg",
    "navLabel": "Nawiguj",
    "coordLabel": "Kopiuj współrzędne"
  },
  {
    "params": [
      51.150085449948264,
      17.019236128378864
    ],
    "status": "open",
    "statusLabel": " Stacja czynna 24/7 ",
    "customLabel": "",
    "adress": "ul. Obornicka 187",
    "city": " Wrocław",
    "price": " 69.00 ",
    "priceLabel": "cena: ",
    "priceUnits": "zł/kg",
    "navLabel": "Nawiguj",
    "coordLabel": "Kopiuj współrzędne"
  },
  {
    "params": [
      52.15255246716199,
      21.010696769396006
    ],
    "status": "open",
    "statusLabel": " Stacja czynna 24/7 ",
    "customLabel": "",
    "adress": "ul. Tango 4",
    "city": "02-825 Warszawa",
    "price": " 69.00 ",
    "priceLabel": "cena: ",
    "priceUnits": "zł/kg",
    "navLabel": "Nawiguj",
    "coordLabel": "Kopiuj współrzędne"
  }
]
```

Monitorowana jest zmiana statusu stacji z open -> * lub * -> open, a w przypadku jakiejkolwiek zmiany wysyłane jest powiadomienie mailem.
Monitorowane są również komunikaty na stronie, a w przypadku jakiejkolwiek zmiany wysyłane są też w powiadomieniu. 

Plik ```previous_state.json``` zawiera ostatni zarejestrowany status stacji.
Plik ```previous_messages.json``` zawiera ostatnio zarejestrowane komunikaty na stronie.

Adresy email znajduja się w secrects repozytorium ```RECEIVER_EMAILS```. Adresy email, które należy pominąć w czasie wysyłki można poprzedzić znakiem ```#``` na początku linii.

Aplikacja wykorzystuje adres Gmail do wysyłania powiadomień, a parametry znajdują się w secrets: ```SMTP_EMAIL```, ```SMTP_PASSWORD```.

Z uwagi na opóźnienia w działaniu Actions/Workflow na GitHub aplikacja jest wyzwalana z zewnątrz przez API i zadanie na cron-job.org (HTTP POST).
