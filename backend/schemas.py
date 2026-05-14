from pydantic import BaseModel

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
