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
    """Pobiera listę odbiorców i dzieli ją na e-mail, telefon i klucz API."""
    emails_raw = os.environ.get("RECEIVER_EMAILS", "")
    if not emails_raw:
        print("Brak skonfigurowanej listy odbiorców w Sekretach.")
        return []

    receivers = []
    for line in emails_raw.splitlines():
        clean_line = line.strip()
        
        # Pomijamy puste linie i te zakomentowane znakiem #
        if clean_line and not clean_line.startswith('#'):
            parts = [p.strip() for p in clean_line.split(',')]
            
            # Bezpieczne przypisywanie zmiennych (nawet jeśli brakuje numeru/klucza)
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
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retries))
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'}
    
    try:
        response = session.get(URL, headers=headers, timeout=(10, 30))
        if response.status_code != 200:
            return None, None
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup, response.text
    except requests.exceptions.RequestException:
        return None, None

def extract_stations(soup):
    script_tag = soup.find('script', id='stations-data')
    if script_tag:
        return json.loads(script_tag.string)
    return []

def extract_messages(soup):
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
    # Wyciągamy same adresy e-mail z listy słowników
    emails = [r['email'] for r in receivers if r.get('email')]
    if not emails:
        return
        
    subject = "ZMIANA STATUSU: Stacje Neso"
    html_body = """<html><body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6; padding: 20px; background-color: #f4f4f4;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.05);">
            <div style="background-color: #0056b3; color: white; padding: 15px 20px;"><h2 style="margin: 0;">Aktualizacja: Stacje Neso</h2></div>
            <div style="padding: 20px;"><ul style="list-style-type: none; padding: 0; margin: 0;">"""
            
    for change in html_changes:
        html_body += f"<li style='margin-bottom: 12px; padding: 12px; background-color: #f8f9fa; border-left: 4px solid #0056b3;'>{change}</li>"
    html_body += """</ul></div></div></body></html>"""

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        for receiver_email in emails:
            msg = MIMEMultipart()
            msg['From'] = f"Monitor Neso <{SENDER_EMAIL}>"
            msg['To'] = receiver_email
            msg['Subject'] = subject
            msg.attach(MIMEText(html_body, 'html', 'utf-8'))
            server.send_message(msg)
            print(f"Wysłano e-mail do: {receiver_email}")
        server.quit()
    except Exception as e:
        print(f"Błąd e-mail: {e}")

def send_whatsapp(wa_changes, receivers):
    if not wa_changes:
        return
        
    message = "🟦 *Aktualizacja: Stacje Neso*\n\n"
    for change in wa_changes:
        message += f"{change}\n\n"
        
    encoded_message = urllib.parse.quote(message)
    
    # Przechodzimy po wszystkich użytkownikach i wysyłamy na WA tylko tym, którzy mają dane
    for r in receivers:
        phone = r.get('wa_phone')
        apikey = r.get('wa_apikey')
        
        if phone and apikey:
            url = f"https://api.callmebot.com/whatsapp.php?phone={phone}&text={encoded_message}&apikey={apikey}"
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    print(f"Wiadomość WhatsApp wysłana do: {phone}")
                else:
                    print(f"Błąd WhatsApp dla {phone}: {response.text}")
            except Exception as e:
                print(f"Błąd połączenia WhatsApp dla {phone}: {e}")

def main():
    soup, raw_text = get_page_data()
    if not soup: return

    html_changes = []
    wa_changes = []

    current_data_raw = extract_stations(soup)
    current_state = {}
    for station in current_data_raw:
        key = f"{station.get('city', '').strip()}, {station.get('adress', '').strip()}"
        current_state[key] = station.get('status')

    previous_state = {}
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            try: previous_state = json.load(f)
            except: pass

    if previous_state:
        for key, new_status in current_state.items():
            old_status = previous_state.get(key)
            if old_status and old_status != new_status:
                if old_status == "open" or new_status == "open":
                    if new_status == "open":
                        html_changes.append(f"✅ <strong>{key}</strong>: Status zmienił się na <span style='color: #28a745; font-weight: bold;'>{new_status.upper()}</span>")
                        wa_changes.append(f"✅ *{key}*: Status zmienił się na 🟢 *{new_status.upper()}*")
                    else:
                        html_changes.append(f"❌ <strong>{key}</strong>: Status zmienił się na <span style='color: #dc3545; font-weight: bold;'>{new_status.upper()}</span>")
                        wa_changes.append(f"❌ *{key}*: Status zmienił się na 🔴 *{new_status.upper()}*")

    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(current_state, f, ensure_ascii=False, indent=2)

    current_messages = extract_messages(soup)
    previous_messages = []
    if os.path.exists(MESSAGES_FILE):
        with open(MESSAGES_FILE, 'r', encoding='utf-8') as f:
            try: previous_messages = json.load(f)
            except: pass

    if os.path.exists(MESSAGES_FILE):
        for msg in current_messages:
            if msg not in previous_messages:
                html_changes.append(f"📣 <span style='color: #d9534f; font-weight: bold;'>NOWY KOMUNIKAT:</span> {msg}")
                wa_changes.append(f"📣 🔴 *NOWY KOMUNIKAT:* {msg}")
        for msg in previous_messages:
            if msg not in current_messages:
                html_changes.append(f"🗑️ <span style='color: #6c757d; font-weight: bold;'>USUNIĘTO KOMUNIKAT:</span> <s style='color: #999;'>{msg}</s>")
                wa_changes.append(f"🗑️ ⚪ *USUNIĘTO KOMUNIKAT:* ~{msg}~")

    with open(MESSAGES_FILE, 'w', encoding='utf-8') as f:
        json.dump(current_messages, f, ensure_ascii=False, indent=2)

    # Wysyłamy, jeśli są jakiekolwiek zmiany (zmieniono logikę na przesyłanie całej listy receivers do obu systemów)
    if html_changes:
        receivers = get_receivers()
        send_email(html_changes, receivers)
        send_whatsapp(wa_changes, receivers)

if __name__ == "__main__":
    main()
