class Book {
    constructor(title, author, genre, description) {
        this.title = title;
        this.author = author;
        this.genre = genre;
        this.description = description;
    }

    static createBook(data) {
        return new Book(data.title, data.author, data.genre, data.description);
    }

    static retrieveBookInfo(book) {
        return {
            title: book.title,
            author: book.author,
            genre: book.genre,
            description: book.description
        };
    }
}

module.exports = Book;