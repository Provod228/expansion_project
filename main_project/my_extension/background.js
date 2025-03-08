chrome.sidePanel
  .setPanelBehavior({ openPanelOnActionClick: true })
  .catch((error) => console.error(error));

chrome.runtime.onInstalled.addListener(() => {
    console.log("Extension installed");
});

// Обработка CORS и безопасности
chrome.webRequest.onHeadersReceived.addListener(
    function(details) {
        let headers = details.responseHeaders;
        headers = headers.filter(header => 
            !(header.name.toLowerCase() === 'x-frame-options' || 
              header.name.toLowerCase() === 'frame-options'));
        
        headers.push({
            name: 'Access-Control-Allow-Origin',
            value: '*'
        });
        headers.push({
            name: 'Access-Control-Allow-Credentials',
            value: 'true'
        });
        headers.push({
            name: 'Access-Control-Allow-Methods',
            value: 'GET, POST, OPTIONS'
        });
        headers.push({
            name: 'Access-Control-Allow-Headers',
            value: 'Content-Type, X-CSRFToken'
        });
        
        return {responseHeaders: headers};
    },
    {
        urls: [
            "http://127.0.0.1:8000/*",
            "http://localhost:8000/*"
        ]
    },
    ["blocking", "responseHeaders", "extraHeaders"]
);

// Слушаем сообщения от sidepanel.html
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === 'serverStatus') {
        // Обновляем иконку в зависимости от статуса сервера
        const iconPath = message.status === 'online' 
            ? 'icons/icon48.png' 
            : 'icons/icon48_offline.png';
        chrome.action.setIcon({ path: iconPath });
    }
    if (message.type === 'logout') {
        // Очищаем все куки для домена приложения
        chrome.cookies.getAll({domain: "localhost"}, function(cookies) {
            for(var i=0; i<cookies.length; i++) {
                chrome.cookies.remove({url: "http://localhost:8000" + cookies[i].path, name: cookies[i].name});
            }
        });
        
        // Очищаем куки для Google аутентификации
        chrome.cookies.getAll({domain: ".google.com"}, function(cookies) {
            for(var i=0; i<cookies.length; i++) {
                chrome.cookies.remove({url: "https://accounts.google.com" + cookies[i].path, name: cookies[i].name});
            }
        });
    }
});

let chatWindowId = null; // Переменная для хранения ID окна чата

chrome.action.onClicked.addListener((tab) => {
    if (chatWindowId) {
        // Если окно уже открыто, закройте его
        chrome.windows.remove(chatWindowId);
        chatWindowId = null; // Сбросить ID окна
    } else {
        // Открыть новое окно чата
        chrome.windows.create({
            url: 'http://localhost:8000/chat/', // URL вашего чата
            type: 'popup',
            width: 500, // Увеличенная ширина окна
            height: 700 // Увеличенная высота окна
        }, (window) => {
            chatWindowId = window.id; // Сохранить ID нового окна
        });
    }
});
