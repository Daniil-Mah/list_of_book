from pydantic import BaseModel
from typing import Optional

# ========== СХЕМЫ ДЛЯ ПОЛЬЗОВАТЕЛЕЙ ==========

class UserBase(BaseModel):
    nickname: str
    role_adm: bool = False

class UserCreate(BaseModel):
    nickname: str
    password: str
    admin_password: Optional[str] = None  # Пароль для получения прав админа

class UserLogin(BaseModel):
    nickname: str
    password: str

class UserOut(UserBase):
    id: int
    is_active: bool
    
    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    nickname: Optional[str] = None
    role_adm: Optional[bool] = None
    is_active: Optional[bool] = None

# ========== СХЕМЫ ДЛЯ АВТОРОВ ==========

class AuthorBase(BaseModel):
    nickname: str

class AuthorCreate(AuthorBase):
    pass

class AuthorUpdate(BaseModel):
    nickname: Optional[str] = None
    is_active: Optional[bool] = None

class AuthorOut(AuthorBase):
    id: int
    is_active: bool
    user_id: int
    
    class Config:
        from_attributes = True

# ========== СХЕМЫ ДЛЯ КНИГ ==========

class BookBase(BaseModel):
    title: str
    author_id: int
    link_of_book: str
    reading_status: bool = True
    bookmark: Optional[str] = None

class BookCreate(BookBase):
    pass

class BookUpdate(BaseModel):
    title: Optional[str] = None
    author_id: Optional[int] = None
    link_of_book: Optional[str] = None
    reading_status: Optional[bool] = None
    bookmark: Optional[str] = None
    is_active: Optional[bool] = None

class BookOut(BookBase):
    id: int
    is_active: bool
    user_id: int
    author_nickname: Optional[str] = None
    
    class Config:
        from_attributes = True