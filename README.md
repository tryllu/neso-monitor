# NESO Monitor
## Aplikacja monitorowania zmian statusów stacji tankowania wodoru Neso.

Aplikacja pobiera stronę https://www.stacjeneso.pl a następnie wyszukuje tag ```stations-data``` zawierający informacje o statusach poszczególnych stacji tankowania wodoru oraz listę komunikatów w klasie ```.section--slider__container```.

Monitorowana jest zmiana statusu stacji z open -> * lub * -> open, a w przypadku jakiejkolwiek zmiany wysyłane jest powiadomienie mailem.
Monitorowane są również komunikaty na stronie, a w przypadku jakiejkolwiek zmiany wysyłane są też w powiadomieniu. 

Plik ```previous_state.json``` zawiera ostatni zarejestrowany status stacji.
Plik ```previous_messages.json``` zawiera ostatnio zarejestrowane komunikaty na stronie.

Adresy email znajduja się w secrects repozytorium ```RECEIVER_EMAILS```. Adresy email, które należy pominąć w czasie wysyłki można poprzedzić znakiem ```#``` na początku linii.

Aplikacja wykorzystuje adres Gmail do wysyłania powiadomień, a parametry znajdują się w secrets: ```SMTP_EMAIL```, ```SMTP_PASSWORD```.

Z uwagi na opóźnienia w działaniu Actions/Workflow na GitHub aplikacja jest wyzwalana z zewnątrz przez API i zadanie na cron-job.org (HTTP POST).
