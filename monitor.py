import requests
from bs4 import BeautifulSoup
import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from requests.adapters import HTTPAdapter, Retry
import urllib.parse

# --- USTAWIENIA ---
URL = "https://stacjeneso.pl"
STATE_FILE = "previous_state.json"
MESSAGES_FILE = "previous_messages.json"
SENDER_EMAIL = os.environ.get("SMTP_EMAIL")
SENDER_PASSWORD = os.environ.get("SMTP_PASSWORD")

def get_receivers():
    """Pobiera listę odbiorców z Sekretów i dzieli na email, telefon i klucz API."""
    emails_raw = os.environ.get("RECEIVER_EMAILS", "")
    
    if not emails_raw:
        print("Brak skonfigurowanej listy odbiorców (Sekret RECEIVER_EMAILS jest pusty).")
        return []

    receivers = []
    for line in emails_raw.splitlines():
        clean_line = line.strip()
        # Ignorujemy linie zaczynające się od #
        if clean_line and not clean_line.startswith('#'):
            # Rozdzielamy po przecinku
            parts = [p.strip() for p in clean_line.split(',')]
            
            # Przypisujemy wartości (nawet jeśli ktoś podał tylko maila bez przecinków)
            email = parts[0]
            wa_phone = parts[1] if len(parts) >= 2 else None
            wa_apikey = parts[2] if len(parts) >= 3 else None
            
            receivers.append({
                'email': email,
                'wa_phone': wa_phone,
                'wa_apikey': wa_apikey
            })
            
    return receivers
    
def get_page_data():
    """Pobiera stronę z włączonym mechanizmem ponawiania i User-Agentem."""
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retries))
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'}
    
    try:
        response = session.get(URL, headers=headers, timeout=(10, 30))
        if response.status_code != 200:
            print(f"Strona zwróciła błąd: {response.status_code}")
            return None, None
        
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup, response.text
    except requests.exceptions.RequestException as e:
        print(f"Błąd połączenia: {e}")
        return None, None

def extract_stations(soup):
    """Wyciąga dane o stacjach z JSON-a w tagu script."""
    script_tag = soup.find('script', id='stations-data')
    if script_tag:
        return json.loads(script_tag.string)
    return []

def extract_messages(soup):
    """Wyciąga komunikaty ze slidera."""
    messages = []
    slider = soup.select_one('.section--slider__container')
    if slider:
        slides = slider.select('.section--slider__container__slide-red')
        for slide in slides:
            text = slide.get_text(strip=True)
            if text:
                messages.append(text)
    return messages

def send_email(html_changes, receivers):
    # Wyciągamy same maile z listy
    emails = [r['email'] for r in receivers if r.get('email')]
    if not emails:
        print("Lista adresów e-mail jest pusta. Pomijam wysyłanie e-maili.")
        return

    subject = "ZMIANA STATUSU: Stacje Neso"
    
    # Budowanie szablonu HTML
    html_body = """
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6; margin: 0; padding: 20px; background-color: #f4f4f4;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border: 1px solid #e0e0e0; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 5px rgba(0,0,0,0.05);">
            <div style="background-color: #0056b3; color: white; padding: 15px 20px;">
                <h2 style="margin: 0; font-size: 20px;">Stacje Neso</h2>
            </div>
            <div style="padding: 20px;">
                <p style="font-size: 16px; margin-top: 0;">Wykryto następujące zmiany w systemie:</p>
                <ul style="list-style-type: none; padding: 0; margin: 0;">
    """
    
    for change in html_changes:
        html_body += f"<li style='margin-bottom: 12px; padding: 12px; background-color: #f8f9fa; border-left: 4px solid #0056b3; border-radius: 4px;'>{change}</li>\n"
        
    html_body += """
                </ul>
            </div>
            <div style="background-color: #f1f1f1; color: #777; font-size: 12px; text-align: center; padding: 12px;">
                Wiadomość wygenerowana automatycznie przez system powiadomień.
            </div>
        </div>
    </body>
    </html>
    """

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        
        for email in emails:
            msg = MIMEMultipart()
            msg['From'] = f"Monitor Neso <{SENDER_EMAIL}>"
            msg['To'] = email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(html_body, 'html', 'utf-8'))
            
            server.send_message(msg)
            print(f"E-mail HTML wysłany pomyślnie do: {receiver}")
            
        server.quit()
    except Exception as e:
        print(f"Błąd wysyłania e-maila: {e}")

def send_whatsapp(wa_changes, receivers):
    if not wa_changes:
        return
        
    message = "🟦 *Aktualizacja: Stacje Neso*\n\n"
    for change in wa_changes:
        message += f"{change}\n\n"
        
    encoded_message = urllib.parse.quote(message)
    
    for r in receivers:
        phone = r.get('wa_phone')
        apikey = r.get('wa_apikey')
        
        # Wysyłamy tylko jeśli użytkownik ma numer i klucz
        if phone and apikey:
            url = f"https://api.callmebot.com/whatsapp.php?phone={phone}&text={encoded_message}&apikey={apikey}"
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    print(f"Wiadomość WhatsApp wysłana do: {phone}")
                else:
                    print(f"Błąd WhatsApp dla {phone}: {response.status_code}")
            except Exception as e:
                print(f"Błąd połączenia WhatsApp dla {phone}: {e}")

def main():
    soup, raw_text = get_page_data()
    if not soup:
        return

    html_changes = []
    wa_changes = []

    # --- 1. SPRAWDZANIE STACJI ---
    current_data_raw = extract_stations(soup)
    current_state = {}
    for station in current_data_raw:
        key = f"{station.get('city', '').strip()}, {station.get('adress', '').strip()}"
        current_state[key] = station.get('status')

    previous_state = {}
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            try:
                previous_state = json.load(f)
            except json.JSONDecodeError:
                pass

    if previous_state:
        for key, new_status in current_state.items():
            old_status = previous_state.get(key)
            if old_status and old_status != new_status:
                if old_status == "open" or new_status == "open":
                    # Formatuje zmianę przy użyciu HTML i emotikon (oryginalne statusy wielkimi literami)
                    if new_status == "open":
                        html_changes.append(f"&#9989; <strong>{key}</strong>: Status zmienił się na <span style='color: #28a745; font-weight: bold;'>{new_status.upper()}</span>")
                        wa_changes.append(f"✅ *{key}*: Status zmienil sie na 🟢 *{new_status.upper()}*")
                    else:
                        html_changes.append(f"&#10060; <strong>{key}</strong>: Status zmienił się na <span style='color: #dc3545; font-weight: bold;'>{new_status.upper()}</span>")
                        wa_changes.append(f"❌ *{key}*: Status zmienil sie na 🔴 *{new_status.upper()}*")

    # Zapisanie nowego stanu stacji
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(current_state, f, ensure_ascii=False, indent=2)


    # --- 2. SPRAWDZANIE KOMUNIKATÓW ---
    current_messages = extract_messages(soup)
    previous_messages = []
    
    if os.path.exists(MESSAGES_FILE):
        with open(MESSAGES_FILE, 'r', encoding='utf-8') as f:
            try:
                previous_messages = json.load(f)
            except json.JSONDecodeError:
                pass

    if os.path.exists(MESSAGES_FILE):
        for msg in current_messages:
            if msg not in previous_messages:
                html_changes.append(f"&#128227; <span style='color: #d9534f; font-weight: bold;'>NOWY KOMUNIKAT:</span> {msg}")
                wa_changes.append(f"📣 🔴 *NOWY KOMUNIKAT:* {msg}")
        
        for msg in previous_messages:
            if msg not in current_messages:
                html_changes.append(f"&#128465; <span style='color: #6c757d; font-weight: bold;'>USUNIĘTO KOMUNIKAT:</span> <s style='color: #999;'>{msg}</s>")
                wa_changes.append(f"🗑️ ⚪ *USUNIETO KOMUNIKAT:* ~{msg}~")

    # Zapisanie nowego stanu komunikatów
    with open(MESSAGES_FILE, 'w', encoding='utf-8') as f:
        json.dump(current_messages, f, ensure_ascii=False, indent=2)


    # --- 3. WYSYŁKA MAILA ---
    if html_changes:
        print("Wykryto zmiany! Pobieram listę adresatów...")
        receivers = get_receivers()
        send_email(html_changes, receivers)
        send_whatsapp(wa_changes, receivers)
    else:
        print("Brak interesujących zmian na stacjach i w komunikatach.")

if __name__ == "__main__":
    main()
