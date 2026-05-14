from fastapi import FastAPI, HTTPException, Depends
from typing import List
from .models import Book
from .schemas import BookCreate, BookUpdate, BookOut
from .db import db

app = FastAPI()

@app.on_event("startup")
def startup():
    db.connect()
    db.create_tables([Book])

@app.on_event("shutdown")
def shutdown():
    db.close()

@app.get("/books/", response_model=List[BookOut])
def list_books(sort_by: str = "id", order: str = "asc"):
    valid_fields = {"id", "title", "author", "year"}
    if sort_by not in valid_fields:
        sort_by = "id"
    if order not in {"asc", "desc"}:
        order = "asc"
    order_by = getattr(getattr(Book, sort_by), order)()
    books = Book.select().order_by(order_by)
    return [BookOut.from_orm(book) for book in books]

@app.post("/books/", response_model=BookOut)
def create_book(book: BookCreate):
    book_obj = Book.create(**book.dict())
    return BookOut.from_orm(book_obj)

@app.delete("/books/{book_id}", response_model=dict)
def delete_book(book_id: int):
    book = Book.get_or_none(Book.id == book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    book.delete_instance()
    return {"ok": True}

@app.put("/books/{book_id}", response_model=BookOut)
def update_book(book_id: int, book_data: BookUpdate):
    book = Book.get_or_none(Book.id == book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    book.title = book_data.title
    book.author = book_data.author
    book.year = book_data.year
    book.save()
    return BookOut.from_orm(book)
