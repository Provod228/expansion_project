chrome.runtime.onInstalled.addListener(() => {
    console.log("Extension installed");
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
