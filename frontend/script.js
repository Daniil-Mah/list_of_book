const API_URL = "http://localhost:8000/books/";

async function loadBooks() {
    const sort_by = document.getElementById('sort_by').value;
    const order = document.getElementById('order').value;
    const res = await fetch(`${API_URL}?sort_by=${sort_by}&order=${order}`);
    const books = await res.json();
    const list = document.getElementById('booksList');
    list.innerHTML = '';
    books.forEach(book => {
        const li = document.createElement('li');
        li.textContent = `${book.id}: "${book.title}" (${book.author}, ${book.year})`;
        const delBtn = document.createElement('button');
        delBtn.textContent = 'Удалить';
        delBtn.onclick = async () => {
            await fetch(API_URL + book.id, {method: 'DELETE'});
            loadBooks();
        };
        const editBtn = document.createElement('button');
        editBtn.textContent = 'Изменить';
        editBtn.onclick = () => editBook(book);
        li.appendChild(delBtn);
        li.appendChild(editBtn);
        list.appendChild(li);
    });
}

document.getElementById('bookForm').onsubmit = async function(e) {
    e.preventDefault();
    const title = document.getElementById('title').value;
    const author = document.getElementById('author').value;
    const year = parseInt(document.getElementById('year').value);
    await fetch(API_URL, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({title, author, year})
    });
    this.reset();
    loadBooks();
};

function editBook(book) {
    document.getElementById('title').value = book.title;
    document.getElementById('author').value = book.author;
    document.getElementById('year').value = book.year;
    const btn = document.querySelector('#bookForm button');
    btn.textContent = 'Обновить';
    document.getElementById('bookForm').onsubmit = async function(e) {
        e.preventDefault();
        const title = document.getElementById('title').value;
        const author = document.getElementById('author').value;
        const year = parseInt(document.getElementById('year').value);
        await fetch(API_URL + book.id, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({title, author, year})
        });
        this.reset();
        btn.textContent = 'Добавить';
        this.onsubmit = defaultSubmit;
        loadBooks();
    };
}
const defaultSubmit = document.getElementById('bookForm').onsubmit;

window.onload = loadBooks;
