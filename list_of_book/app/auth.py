from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .models import Users
import secrets
import os
from dotenv import load_dotenv

load_dotenv()

# Константа для административного пароля из .env
ADMIN_SECRET_PASSWORD = os.getenv('ADMIN_SECRET_PASSWORD', 'SecretAdminPassword123')

# Схема безопасности для токена
security = HTTPBearer()

# Хранилище токенов (в реальном проекте используйте Redis или БД)
active_tokens = {}

# Функция для генерации токена
def generate_token(user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    active_tokens[token] = user_id
    return token

# Функция для удаления токена
def revoke_token(token: str):
    if token in active_tokens:
        del active_tokens[token]

# Получение текущего пользователя по токену
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    
    if token not in active_tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = active_tokens[token]
    user = Users.get_or_none(Users.id == user_id)
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    return user

# Проверка прав администратора
async def get_current_admin(current_user: Users = Depends(get_current_user)):
    if not current_user.role_adm:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user