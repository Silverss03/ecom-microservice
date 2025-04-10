// Sample book data
const books = [
    { id: 1, title: "To Kill a Mockingbird", author: "Harper Lee", genre: "fiction" },
    { id: 2, title: "1984", author: "George Orwell", genre: "fiction" },
    { id: 3, title: "The Great Gatsby", author: "F. Scott Fitzgerald", genre: "fiction" },
    { id: 4, title: "Pride and Prejudice", author: "Jane Austen", genre: "romance" },
    { id: 5, title: "Murder on the Orient Express", author: "Agatha Christie", genre: "mystery" },
    { id: 6, title: "The Hobbit", author: "J.R.R. Tolkien", genre: "fantasy" },
    { id: 7, title: "Harry Potter and the Sorcerer's Stone", author: "J.K. Rowling", genre: "fantasy" },
    { id: 8, title: "A Brief History of Time", author: "Stephen Hawking", genre: "non-fiction" },
    { id: 9, title: "Sapiens", author: "Yuval Noah Harari", genre: "non-fiction" },
    { id: 10, title: "The Da Vinci Code", author: "Dan Brown", genre: "thriller" }
];

function getRecommendations(genre, limit = 3) {
    // If genre is provided, filter by genre
    const filteredBooks = genre 
        ? books.filter(book => book.genre.toLowerCase() === genre.toLowerCase())
        : books;
        
    // Shuffle array to get random recommendations
    const shuffled = [...filteredBooks].sort(() => 0.5 - Math.random());
    
    // Return up to the limit
    return shuffled.slice(0, limit);
}

module.exports = {
    getRecommendations
};