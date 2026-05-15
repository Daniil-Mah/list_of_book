from fastapi import FastAPI, HTTPException, Query
from typing import List, Optional
from .models import Users, Author, Books
from .schemas import BookCreate, BookUpdate, BookOut, UserCreate, UserOut, AuthorCreate, AuthorOut
from .db import db

app = FastAPI()

@app.on_event("startup")
def startup():
    db.connect()
    db.create_tables([Users, Author, Books])

@app.on_event("shutdown")
def shutdown():
    db.close()

@app.get("/books/", response_model=List[BookOut])
def list_books(
    sort_by: str = "id",
    order: str = "asc",
    title: Optional[str] = None,
    author: Optional[str] = None,
    tag: Optional[str] = None):

    valid_fields = {"id", "title", "author_id", "reading_status"}
    if sort_by not in valid_fields:
        sort_by = "id"
    if order not in {"asc", "desc"}:
        order = "asc"
    query = Books.select()

    if title:
        query = query.where(Books.title.contains(title))
    if author:
        query = query.join(Author).where(Author.nickname.contains(author))

    order_by = getattr(getattr(Books, sort_by), order)()
    books = query.order_by(order_by)
    return [BookOut.from_attributes == True for book in books]

@app.post("/books/", response_model=BookOut)
def create_book(book: BookCreate):
    book_obj = Books.create(**book.dict())
    return BookOut.from_attributes == True

@app.delete("/books/{book_id}", response_model=dict)
def delete_book(book_id: int):
    book = Books.get_or_none(Books.id == book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    book.delete_instance()
    return {"ok": True}

@app.put("/books/{book_id}", response_model=BookOut)
def update_book(book_id: int, book_data: BookUpdate):
    book = Books.get_or_none(Books.id == book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    for field, value in book_data.dict().items():
        setattr(book, field, value)
    book.save()
    return BookOut.from_attributes == True


@app.post("/users/register", response_model=UserOut)
def register_user(user: UserCreate):
    if Users.get_or_none(Users.nickname == user.nickname):
        raise HTTPException(status_code=400, detail="Nickname already exists")
    user_obj = Users.create(nickname=user.nickname, password=user.password)
    return UserOut.from_attributes == True

@app.post("/authors/", response_model=AuthorOut)
def create_author(author: AuthorCreate):
    if Author.get_or_none(Author.nickname == author.nickname):
        raise HTTPException(status_code=400, detail="Author already exists")
    author_obj = Author.create(nickname=author.nickname)
    return AuthorOut.from_attributes == True

@app.get("/authors/", response_model=List[AuthorOut])
def list_authors():
    authors = Author.select()
    return [AuthorOut.from_attributes == True for author in authors]

@app.delete("/authors/{author_id}", response_model=dict)
def delete_author(author_id: int):
    author = Author.get_or_none(Author.id == author_id)
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    author.delete_instance(recursive=True)
    return {"ok": True}

if __name__ == '__main__':
    pass