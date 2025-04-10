const intents = {
    GREETING: {
        intent: "greeting",
        examples: [
            "Hello",
            "Hi",
            "Hey",
            "Good morning",
            "Good evening"
        ]
    },
    BOOK_RECOMMENDATION: {
        intent: "book_recommendation",
        examples: [
            "Can you recommend a book?",
            "I need a book suggestion",
            "What book should I read?",
            "Suggest me a book",
            "Any good books to read?"
        ]
    },
    FEEDBACK: {
        intent: "feedback",
        examples: [
            "I liked that recommendation",
            "That was helpful",
            "Thanks for the suggestion",
            "I didn't like that book"
        ]
    },
    GOODBYE: {
        intent: "goodbye",
        examples: [
            "Goodbye",
            "See you later",
            "Bye",
            "Take care"
        ]
    },
    
    // Add these properties to match what bot.js is looking for
    greeting: "greeting",
    recommendation: "recommendation", 
    default: "default"
};

module.exports = intents;