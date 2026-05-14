from pydantic import BaseModel

class UserBase(BaseModel):
    nickname: str

class UserCreate(UserBase):
    password: str

class UserOut(UserBase):
    id: int
    role_adm: bool
    class Config:
        orm_mode = True


class AuthorBase(BaseModel):
    nickname: str

class AuthorCreate(AuthorBase):
    pass

class AuthorOut(AuthorBase):
    id: int
    class Config:
        orm_mode = True

class TagsBase(BaseModel):
    tag: str

class TagsCreate(TagsBase):
    pass

class TagsOut(TagsBase):
    id: int
    class Config:
        orm_mode = True


class BookBase(BaseModel):
    title: str
    author_id: int
    link_of_book: str
    reading_status: bool = True
    bookmark: str
    tegs_id: int

class BookCreate(BookBase):
    pass

class BookUpdate(BaseModel):
    title: str
    author_id: int
    link_of_book: str
    reading_status: bool
    bookmark: str
    tegs_id: int

class BookOut(BookBase):
    id: int

    class Config:
        orm_mode = True
