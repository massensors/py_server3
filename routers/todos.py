from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import Todos
from pydantic import BaseModel, Field

router = APIRouter(
    prefix="/todos",
    tags=["todos"],
    responses={404: {"description": "Not found"}},
)

class TodoRequest(BaseModel):
    """Model Pydantic dla żądań """
    title: str = Field(min_length=3)
    description: str = Field(min_length=3, max_length=100)
    priority: int = Field(gt=0, lt=6)
    complete: bool

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Przykładowe zadanie",
                "description": "Opis przykładowego zadania",
                "priority": 1,
                "complete": False
            }
        }

class TodoResponse(BaseModel):
    """Model Pydantic dla odpowiedzi """
    id: int
    title: str
    description: str
    priority: int
    complete: bool

    class Config:
        from_attributes = True

@router.get("/", response_model=List[TodoResponse])
async def read_all_todos(db: Session = Depends(get_db)):
    """Pobierz wszystkie zadania"""
    return db.query(Todos).all()

@router.get("/{todo_id}", response_model=TodoResponse)
async def read_todo(todo_id: int, db: Session = Depends(get_db)):
    """Pobierz zadanie po ID"""
    todo_model = db.query(Todos).filter(Todos.id == todo_id).first()
    if todo_model is None:
        raise HTTPException(status_code=404, detail="Zadanie nie znalezione")
    return todo_model

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_todo(todo_request: TodoRequest, db: Session = Depends(get_db)):
    """Utwórz nowe zadanie"""
    todo_model = Todos(**todo_request.model_dump())
    db.add(todo_model)
    db.commit()
    return {"status": "success", "message": "Zadanie utworzone"}