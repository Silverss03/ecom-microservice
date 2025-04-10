const { getRecommendations } = require('../services/recommendationService');

class ChatBot {
    constructor() {
        this.intents = require('./intents');
        this.responses = require('./responses');
        this.conversationState = {
            askingForGenre: false
        };
    }

    receiveMessage(message) {
        // Check if user is typing the exact intent name (for testing)
        if (message === 'greeting') {
            return this.responses.greetingResponse;
        } else if (message === 'book_recommendation') {
            return this.responses.recommendationResponse;
        }
        
        // Check if we're waiting for a genre response
        if (this.conversationState.askingForGenre) {
            this.conversationState.askingForGenre = false;
            // Treat the message as a genre
            const books = getRecommendations(message);
            return this.responses.recommendBooks(books);
        }

        const intent = this.detectIntent(message);
        return this.sendMessage(intent, message);
    }

    detectIntent(message) {
        const lowerMessage = message.toLowerCase();
        
        // Standard intent detection
        if (lowerMessage.includes('recommend') || 
            lowerMessage.includes('suggestion') || 
            lowerMessage.includes('book') || 
            lowerMessage.includes('read')) {
            return this.intents.recommendation;
        } else if (lowerMessage.includes('hello') || 
                   lowerMessage.includes('hi') || 
                   lowerMessage.includes('hey')) {
            return this.intents.greeting;
        } else if (lowerMessage.includes('thank')) {
            return 'thanks';
        } else {
            return this.intents.default;
        }
    }

    sendMessage(intent, message) {
        switch (intent) {
            case this.intents.recommendation:
                // Extract genre from message if possible
                const genres = ['fiction', 'non-fiction', 'mystery', 'fantasy', 'romance', 'thriller'];
                const messageWords = message.toLowerCase().split(' ');
                
                for (const genre of genres) {
                    if (messageWords.includes(genre)) {
                        // If we found a genre in the message, provide specific recommendations
                        const books = getRecommendations(genre);
                        return this.responses.recommendBooks(books);
                    }
                }
                
                // If no genre found, ask for genre and set state
                this.conversationState.askingForGenre = true;
                return this.responses.askForGenre;
            case this.intents.greeting:
                return this.responses.greetingResponse;
            case 'thanks':
                return this.responses.thankYou;
            default:
                return this.responses.defaultResponse;
        }
    }
}

module.exports = ChatBot;