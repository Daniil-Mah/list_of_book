from fastapi import FastAPI, HTTPException, Query, Depends, status
from typing import List, Optional
from peewee import DoesNotExist
from .models import Users, Author, Books
from .schemas import (
    BookCreate, BookUpdate, BookOut,
    UserCreate, UserOut, UserLogin, UserUpdate,
    AuthorCreate, AuthorOut, AuthorUpdate
)
from .db import db
from .auth import get_current_user, get_current_admin, generate_token, ADMIN_SECRET_PASSWORD

app = FastAPI(title="Book Manager API", version="2.0", docs_url="/docs", redoc_url="/redoc")

# ========== НАСТРОЙКА БАЗЫ ДАННЫХ ==========

@app.on_event("startup")
def startup():
    """Действия при запуске приложения"""
    if db.is_closed():
        db.connect()
    db.create_tables([Users, Author, Books], safe=True)
    print("✅ База данных успешно подключена и готова к работе")

@app.on_event("shutdown")
def shutdown():
    """Действия при остановке приложения"""
    if not db.is_closed():
        db.close()
    print("👋 Приложение остановлено, соединение с БД закрыто")

# ========== АУТЕНТИФИКАЦИЯ И РЕГИСТРАЦИЯ ==========

@app.post("/auth/register", response_model=dict)
def register_user(user: UserCreate):
    """
    Регистрация нового пользователя
    - Если указан правильный admin_password - пользователь получает права администратора
    """
    if Users.get_or_none(Users.nickname == user.nickname):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким nickname уже существует"
        )
    
    # Определяем, становится ли пользователь администратором
    is_admin = False
    if user.admin_password and user.admin_password == ADMIN_SECRET_PASSWORD:
        is_admin = True
    
    # Создаем нового пользователя
    new_user = Users.create(
        nickname=user.nickname,
        password=user.password,
        role_adm=is_admin,
        is_active=True
    )
    
    token = generate_token(new_user.id)
    
    return {
        "message": "✅ Регистрация успешно завершена",
        "user_id": new_user.id,
        "nickname": new_user.nickname,
        "role": "admin" if is_admin else "user",
        "token": token
    }

@app.post("/auth/login", response_model=dict)
def login_user(user: UserLogin):
    """Авторизация пользователя"""
    db_user = Users.get_or_none(Users.nickname == user.nickname)
    
    if not db_user or db_user.password != user.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный nickname или пароль"
        )
    
    if not db_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ваш аккаунт деактивирован. Обратитесь к администратору"
        )
    
    token = generate_token(db_user.id)
    
    return {
        "message": "✅ Вход выполнен успешно",
        "user_id": db_user.id,
        "nickname": db_user.nickname,
        "role": "admin" if db_user.role_adm else "user",
        "token": token
    }

@app.post("/auth/logout", response_model=dict)
def logout_user(current_user: Users = Depends(get_current_user)):
    """Выход из системы"""
    return {"message": "✅ Выход выполнен успешно"}

# ========== КНИГИ ==========

@app.get("/books/", response_model=List[BookOut])
def list_books(
    title: Optional[str] = Query(None, description="Фильтр по названию"),
    author_name: Optional[str] = Query(None, description="Фильтр по автору"),
    reading_status: Optional[bool] = Query(None, description="Фильтр по статусу чтения"),
    show_inactive: bool = Query(False, description="Показывать неактивные (только админ)"),
    sort_by: str = Query("id", regex="^(id|title|reading_status|author_nickname)$"),
    order: str = Query("asc", regex="^(asc|desc)$"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: Users = Depends(get_current_user)
):
    """Получение списка книг с фильтрацией и сортировкой"""
    show_inactive_access = show_inactive and current_user.role_adm
    
    if current_user.role_adm and not show_inactive_access:
        query = Books.select().join(Author).where(Books.is_active == True)
    elif current_user.role_adm and show_inactive_access:
        query = Books.select().join(Author)
    else:
        query = Books.select().join(Author).where(
            (Books.user == current_user.id) & (Books.is_active == True)
        )
    
    if title:
        query = query.where(Books.title.contains(title))
    if author_name:
        query = query.where(Author.nickname.contains(author_name))
    if reading_status is not None:
        query = query.where(Books.reading_status == reading_status)
    
    if sort_by == "author_nickname":
        if order == "asc":
            query = query.order_by(Author.nickname.asc())
        else:
            query = query.order_by(Author.nickname.desc())
    else:
        if order == "asc":
            query = query.order_by(getattr(Books, sort_by).asc())
        else:
            query = query.order_by(getattr(Books, sort_by).desc())
    
    books = query.limit(limit).offset(offset)
    
    result = []
    for book in books:
        book_out = BookOut.model_validate(book)
        book_out.author_nickname = book.author.nickname
        book_out.user_id = book.user.id
        result.append(book_out)
    
    return result

@app.get("/books/search/", response_model=List[BookOut])
def search_books(
    query: str = Query(..., min_length=1),
    search_in: str = Query("title", regex="^(title|author)$"),
    current_user: Users = Depends(get_current_user)
):
    """Поиск книг по названию или автору"""
    if current_user.role_adm:
        base_query = Books.select().join(Author).where(Books.is_active == True)
    else:
        base_query = Books.select().join(Author).where(
            (Books.user == current_user.id) & (Books.is_active == True)
        )
    
    if search_in == "title":
        books = base_query.where(Books.title.contains(query))
    else:
        books = base_query.where(Author.nickname.contains(query))
    
    result = []
    for book in books:
        book_out = BookOut.model_validate(book)
        book_out.author_nickname = book.author.nickname
        book_out.user_id = book.user.id
        result.append(book_out)
    
    return result

@app.get("/books/{book_id}", response_model=BookOut)
def get_book(book_id: int, current_user: Users = Depends(get_current_user)):
    """Получение конкретной книги"""
    try:
        book = Books.select().join(Author).where(Books.id == book_id).get()
        
        if not current_user.role_adm and book.user.id != current_user.id:
            raise HTTPException(status_code=403, detail="Нет доступа")
        
        if not current_user.role_adm and not book.is_active:
            raise HTTPException(status_code=404, detail="Книга не найдена")
        
        book_out = BookOut.model_validate(book)
        book_out.author_nickname = book.author.nickname
        book_out.user_id = book.user.id
        return book_out
    except DoesNotExist:
        raise HTTPException(status_code=404, detail="Книга не найдена")

@app.post("/books/", response_model=BookOut)
def create_book(book: BookCreate, current_user: Users = Depends(get_current_user)):
    """Создание новой книги"""
    author = Author.get_or_none(Author.id == book.author_id)
    
    if not author:
        raise HTTPException(status_code=404, detail="Автор не найден")
    
    if not current_user.role_adm and author.user.id != current_user.id:
        raise HTTPException(status_code=403, detail="Можно создавать книги только для своих авторов")
    
    new_book = Books.create(
        title=book.title,
        author=author,
        link_of_book=book.link_of_book,
        reading_status=book.reading_status,
        bookmark=book.bookmark,
        user=current_user if not current_user.role_adm else author.user,
        is_active=True
    )
    
    book_out = BookOut.model_validate(new_book)
    book_out.author_nickname = author.nickname
    book_out.user_id = new_book.user.id
    return book_out

@app.put("/books/{book_id}", response_model=BookOut)
def update_book(book_id: int, book_data: BookUpdate, current_user: Users = Depends(get_current_user)):
    """Полное обновление книги"""
    book = Books.get_or_none(Books.id == book_id)
    
    if not book:
        raise HTTPException(status_code=404, detail="Книга не найдена")
    
    if not current_user.role_adm and book.user.id != current_user.id:
        raise HTTPException(status_code=403, detail="Нет прав на редактирование")
    
    if book_data.author_id is not None:
        new_author = Author.get_or_none(Author.id == book_data.author_id)
        if not new_author:
            raise HTTPException(status_code=404, detail="Новый автор не найден")
        if not current_user.role_adm and new_author.user.id != current_user.id:
            raise HTTPException(status_code=403, detail="Можно привязывать только к своим авторам")
        book.author = new_author
    
    update_data = book_data.model_dump(exclude_unset=True, exclude={'author_id'})
    for field, value in update_data.items():
        setattr(book, field, value)
    
    book.save()
    
    book_out = BookOut.model_validate(book)
    book_out.author_nickname = book.author.nickname
    book_out.user_id = book.user.id
    return book_out

@app.delete("/books/{book_id}", response_model=dict)
def delete_book(
    book_id: int,
    permanent: bool = Query(False),
    current_user: Users = Depends(get_current_user)
):
    """Удаление книги (мягкое или полное)"""
    book = Books.get_or_none(Books.id == book_id)
    
    if not book:
        raise HTTPException(status_code=404, detail="Книга не найдена")
    
    if not current_user.role_adm and book.user.id != current_user.id:
        raise HTTPException(status_code=403, detail="Нет прав на удаление")
    
    if permanent and current_user.role_adm:
        book.delete_instance(recursive=True)
        return {"message": "Книга полностью удалена"}
    else:
        book.is_active = False
        book.save()
        return {"message": "Книга перемещена в корзину"}

@app.post("/books/{book_id}/restore", response_model=dict)
def restore_book(book_id: int, current_user: Users = Depends(get_current_user)):
    """Восстановление книги из корзины"""
    book = Books.get_or_none(Books.id == book_id)
    
    if not book:
        raise HTTPException(status_code=404, detail="Книга не найдена")
    
    if not current_user.role_adm and book.user.id != current_user.id:
        raise HTTPException(status_code=403, detail="Нет прав на восстановление")
    
    if book.is_active:
        raise HTTPException(status_code=400, detail="Книга уже активна")
    
    book.is_active = True
    book.save()
    return {"message": "Книга восстановлена"}

# ========== АВТОРЫ ==========

@app.get("/authors/", response_model=List[AuthorOut])
def list_authors(
    nickname: Optional[str] = Query(None),
    show_inactive: bool = Query(False),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: Users = Depends(get_current_user)
):
    """Получение списка авторов"""
    if current_user.role_adm and not show_inactive:
        query = Author.select().where(Author.is_active == True)
    elif current_user.role_adm and show_inactive:
        query = Author.select()
    else:
        query = Author.select().where(
            (Author.user == current_user.id) & (Author.is_active == True)
        )
    
    if nickname:
        query = query.where(Author.nickname.contains(nickname))
    
    authors = query.limit(limit).offset(offset)
    return [AuthorOut.model_validate(author) for author in authors]

@app.get("/authors/{author_id}", response_model=AuthorOut)
def get_author(author_id: int, current_user: Users = Depends(get_current_user)):
    """Получение конкретного автора"""
    author = Author.get_or_none(Author.id == author_id)
    
    if not author:
        raise HTTPException(status_code=404, detail="Автор не найден")
    
    if not current_user.role_adm and author.user.id != current_user.id:
        raise HTTPException(status_code=403, detail="Нет доступа")
    
    if not current_user.role_adm and not author.is_active:
        raise HTTPException(status_code=404, detail="Автор не найден")
    
    return AuthorOut.model_validate(author)

@app.post("/authors/", response_model=AuthorOut)
def create_author(author: AuthorCreate, current_user: Users = Depends(get_current_user)):
    """Создание нового автора"""
    existing = Author.get_or_none(
        (Author.nickname == author.nickname) & (Author.user == current_user.id)
    )
    
    if existing:
        raise HTTPException(status_code=400, detail="Автор уже существует")
    
    new_author = Author.create(
        nickname=author.nickname,
        user=current_user,
        is_active=True
    )
    
    return AuthorOut.model_validate(new_author)

@app.put("/authors/{author_id}", response_model=AuthorOut)
def update_author(author_id: int, author_data: AuthorUpdate, current_user: Users = Depends(get_current_user)):
    """Обновление автора"""
    author = Author.get_or_none(Author.id == author_id)
    
    if not author:
        raise HTTPException(status_code=404, detail="Автор не найден")
    
    if not current_user.role_adm and author.user.id != current_user.id:
        raise HTTPException(status_code=403, detail="Нет прав")
    
    update_data = author_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(author, field, value)
    
    author.save()
    return AuthorOut.model_validate(author)

@app.delete("/authors/{author_id}", response_model=dict)
def delete_author(
    author_id: int,
    permanent: bool = Query(False),
    current_user: Users = Depends(get_current_user)
):
    """Удаление автора"""
    author = Author.get_or_none(Author.id == author_id)
    
    if not author:
        raise HTTPException(status_code=404, detail="Автор не найден")
    
    if not current_user.role_adm and author.user.id != current_user.id:
        raise HTTPException(status_code=403, detail="Нет прав")
    
    if permanent and current_user.role_adm:
        Books.delete().where(Books.author == author_id).execute()
        author.delete_instance()
        return {"message": "Автор полностью удален"}
    else:
        author.is_active = False
        author.save()
        Books.update(is_active=False).where(Books.author == author_id).execute()
        return {"message": "Автор и его книги перемещены в корзину"}

@app.post("/authors/{author_id}/restore", response_model=dict)
def restore_author(author_id: int, current_user: Users = Depends(get_current_user)):
    """Восстановление автора"""
    author = Author.get_or_none(Author.id == author_id)
    
    if not author:
        raise HTTPException(status_code=404, detail="Автор не найден")
    
    if not current_user.role_adm and author.user.id != current_user.id:
        raise HTTPException(status_code=403, detail="Нет прав")
    
    if author.is_active:
        raise HTTPException(status_code=400, detail="Автор уже активен")
    
    author.is_active = True
    author.save()
    Books.update(is_active=True).where(Books.author == author_id).execute()
    return {"message": "Автор и его книги восстановлены"}

# ========== ПОЛЬЗОВАТЕЛИ (ТОЛЬКО АДМИН) ==========

@app.get("/admin/users/", response_model=List[UserOut])
def list_users(
    nickname: Optional[str] = Query(None),
    show_inactive: bool = Query(False),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_admin: Users = Depends(get_current_admin)
):
    """Список всех пользователей (только админ)"""
    if show_inactive:
        query = Users.select()
    else:
        query = Users.select().where(Users.is_active == True)
    
    if nickname:
        query = query.where(Users.nickname.contains(nickname))
    
    users = query.limit(limit).offset(offset)
    return [UserOut.model_validate(user) for user in users]

@app.get("/admin/users/{user_id}", response_model=UserOut)
def get_user(user_id: int, current_admin: Users = Depends(get_current_admin)):
    """Получение пользователя по ID (только админ)"""
    user = Users.get_or_none(Users.id == user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    return UserOut.model_validate(user)

@app.put("/admin/users/{user_id}", response_model=UserOut)
def update_user(user_id: int, user_data: UserUpdate, current_admin: Users = Depends(get_current_admin)):
    """Обновление пользователя (только админ)"""
    user = Users.get_or_none(Users.id == user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    update_data = user_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    user.save()
    return UserOut.model_validate(user)

@app.delete("/admin/users/{user_id}", response_model=dict)
def delete_user(
    user_id: int,
    permanent: bool = Query(False),
    current_admin: Users = Depends(get_current_admin)
):
    """Удаление пользователя (только админ)"""
    user = Users.get_or_none(Users.id == user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    if user.id == current_admin.id:
        raise HTTPException(status_code=400, detail="Нельзя удалить себя")
    
    if permanent:
        Books.delete().where(Books.user == user_id).execute()
        Author.delete().where(Author.user == user_id).execute()
        user.delete_instance()
        return {"message": f"Пользователь {user.nickname} полностью удален"}
    else:
        user.is_active = False
        user.save()
        Books.update(is_active=False).where(Books.user == user_id).execute()
        Author.update(is_active=False).where(Author.user == user_id).execute()
        return {"message": f"Пользователь {user.nickname} деактивирован"}

@app.post("/admin/users/{user_id}/restore", response_model=dict)
def restore_user(user_id: int, current_admin: Users = Depends(get_current_admin)):
    """Восстановление пользователя (только админ)"""
    user = Users.get_or_none(Users.id == user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    if user.is_active:
        raise HTTPException(status_code=400, detail="Пользователь уже активен")
    
    user.is_active = True
    user.save()
    Books.update(is_active=True).where(Books.user == user_id).execute()
    Author.update(is_active=True).where(Author.user == user_id).execute()
    return {"message": f"Пользователь {user.nickname} восстановлен"}

# ========== СТАТИСТИКА ==========

@app.get("/stats/")
def get_stats(current_user: Users = Depends(get_current_user)):
    """Получение статистики"""
    if current_user.role_adm:
        total_books = Books.select().count()
        active_books = Books.select().where(Books.is_active == True).count()
        total_authors = Author.select().count()
        active_authors = Author.select().where(Author.is_active == True).count()
        total_users = Users.select().count()
        active_users = Users.select().where(Users.is_active == True).count()
    else:
        total_books = Books.select().where(Books.user == current_user.id).count()
        active_books = Books.select().where(
            (Books.user == current_user.id) & (Books.is_active == True)
        ).count()
        total_authors = Author.select().where(Author.user == current_user.id).count()
        active_authors = Author.select().where(
            (Author.user == current_user.id) & (Author.is_active == True)
        ).count()
        total_users = 1
        active_users = 1 if current_user.is_active else 0
    
    reading_books = Books.select().where(
        (Books.reading_status == True) & (Books.is_active == True)
    )
    if not current_user.role_adm:
        reading_books = reading_books.where(Books.user == current_user.id)
    
    return {
        "total_books": total_books,
        "active_books": active_books,
        "reading_books": reading_books.count(),
        "total_authors": total_authors,
        "active_authors": active_authors,
        "total_users": total_users,
        "active_users": active_users
    }