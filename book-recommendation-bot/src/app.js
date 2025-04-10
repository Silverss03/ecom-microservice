const express = require('express');
const bodyParser = require('body-parser');
const  ChatBot  = require('./chatbot/bot');
const { getRecommendations } = require('./services/recommendationService');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(bodyParser.json());
app.use(express.static('public'));

const chatbot = new ChatBot();

app.post('/chat', (req, res) => {
    const userMessage = req.body.message;
    const response = chatbot.receiveMessage(userMessage);
    res.json({ response });
});

app.get('/recommendations/:genre', (req, res) => {
    const genre = req.params.genre;
    const recommendations = getRecommendations(genre);
    res.json({ recommendations });
});

app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
});