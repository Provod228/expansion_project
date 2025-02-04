chrome.runtime.onInstalled.addListener(() => {
    console.log("Extension installed");
});

chrome.action.onClicked.addListener((tab) => {
    chrome.windows.create({
        url: 'http://localhost:8000/chat/',
        type: 'popup',
        width: 400, // Ширина окна
        height: 600 // Высота окна
    });
});
