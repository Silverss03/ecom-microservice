const responses = {
    greeting: "Hello! I'm here to help you find your next great read",
    // Add missing properties that bot.js is looking for
    greetingResponse: "Hello! I'm here to help you find your next great read",
    recommendationResponse: "I recommend 'The Great Gatsby' by F. Scott Fitzgerald, 'To Kill a Mockingbird' by Harper Lee, and '1984' by George Orwell.",
    defaultResponse: "I'm sorry, I didn't quite understand that. Can you please rephrase?",
    
    // Keep existing properties
    askForGenre: "Please tell me a genre you're interested in, such as fiction, non-fiction, mystery, or fantasy.",
    recommendBooks: (books) => {
        if (books.length === 0) {
            return "I'm sorry, but I couldn't find any books in that genre.";
        }
        const bookList = books.map(book => `${book.title} by ${book.author}`).join(", ");
        return `Here are some recommendations for you: ${bookList}.`;
    },
    fallback: "I'm sorry, I didn't quite understand that. Can you please rephrase?",
    thankYou: "You're welcome! If you need more recommendations, just let me know.",
};

module.exports = responses;