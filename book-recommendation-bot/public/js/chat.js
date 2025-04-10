const chatContainer = document.getElementById('chat-container');
const userInput = document.getElementById('user-input');
const sendButton = document.getElementById('send-button');

sendButton.addEventListener('click', sendMessage);

function sendMessage() {
    const message = userInput.value;
    if (message.trim() === '') return;

    displayMessage('User', message);
    userInput.value = '';

    fetch('/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message }),
    })
    .then(response => response.json())
    .then(data => {
        displayMessage('Bot', data.response);
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

function displayMessage(sender, message) {
    const messageElement = document.createElement('div');
    messageElement.classList.add('message');
    messageElement.classList.add(sender.toLowerCase());
    messageElement.textContent = `${sender}: ${message}`;
    chatContainer.appendChild(messageElement);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}