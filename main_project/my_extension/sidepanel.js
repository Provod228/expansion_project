async function checkServer() {
    try {
        const response = await fetch('http://127.0.0.1:8000/chat/', {
            method: 'GET',
            headers: {
                'Accept': 'text/html',
                'Content-Type': 'text/html; charset=utf-8'
            },
            mode: 'cors',
            credentials: 'include'
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        document.getElementById('loading').style.display = 'none';
        document.getElementById('error-message').style.display = 'none';
        document.getElementById('chatFrame').style.display = 'block';
        
    } catch (error) {
        console.error('Server check failed:', error);
        document.getElementById('loading').style.display = 'none';
        document.getElementById('error-message').style.display = 'block';
        document.getElementById('error-message').textContent = 'Ошибка подключения к серверу';
    }
}

// Запускаем проверку сервера только при загрузке страницы
document.addEventListener('DOMContentLoaded', checkServer);

// Обработчик сообщений
window.addEventListener('message', function(event) {
    if (event.origin === 'http://127.0.0.1:8000') {
        if (event.data.type === 'logout') {
            document.getElementById('chatFrame').src = 'http://127.0.0.1:8000/accounts/login/';
        }
    }
});

// Обработчик сообщений от окна авторизации
window.addEventListener('message', function(event) {
    if (event.origin === 'http://localhost:8000') {
        if (event.data.type === 'auth_success') {
            // Перезагружаем фрейм после успешной авторизации
            document.getElementById('chatFrame').contentWindow.location.reload();
            
            // Закрываем все окна авторизации
            chrome.windows.getAll({ windowTypes: ['popup'] }, function(windows) {
                windows.forEach(function(window) {
                    chrome.windows.remove(window.id);
                });
            });
        } else if (event.data.type === 'logout_success') {
            // Очищаем фрейм при выходе
            document.getElementById('chatFrame').contentWindow.location.reload();
        }
    }
});

// Добавляем обработчик для кнопки входа через Google
document.addEventListener('DOMContentLoaded', function() {
    const loginButton = document.getElementById('login-button');
    if (loginButton) {
        loginButton.addEventListener('click', function(e) {
            e.preventDefault();
            // Открываем окно авторизации Google в новом окне
            chrome.windows.create({
                url: 'http://localhost:8000/accounts/google/login/',
                type: 'popup',
                width: 600,
                height: 700
            });
        });
    }
});

// Функция проверки авторизации
async function checkAuth() {
    try {
        const response = await fetch('http://127.0.0.1:8000/chat/', {
            credentials: 'include'
        });
        
        if (!response.ok) {
            document.getElementById('chatFrame').style.display = 'none';
            document.getElementById('loading').style.display = 'block';
            document.getElementById('error-message').style.display = 'none';
        } else {
            document.getElementById('chatFrame').style.display = 'block';
            document.getElementById('loading').style.display = 'none';
            document.getElementById('error-message').style.display = 'none';
        }
    } catch (error) {
        console.error('Auth check error:', error);
    }
}

// Вместо этого проверяем авторизацию только при:
// 1. Загрузке страницы
document.addEventListener('DOMContentLoaded', checkAuth);

// 2. После успешной авторизации
window.addEventListener('message', function(event) {
    if (event.origin === 'http://localhost:8000') {
        if (event.data.type === 'auth_success') {
            checkAuth();
        }
    }
}); 