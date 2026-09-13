from fastapi import APIRouter, Depends, HTTPException, status
from backend.app.dependencies import get_current_user
from backend.core.exceptions import ValidationException
from backend.core.security import create_access_token, hash_password, verify_password
from backend.database.repositories.user_repo import user_repo
from backend.models.user import Token, UserCreate, UserLogin, UserOut

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserOut)
async def register(user_in: UserCreate):
    existing = await user_repo.get_by_username(user_in.username)
    if existing:
        raise ValidationException("Username already exists.")

    hashed_pw = hash_password(user_in.password)
    user_out = await user_repo.create(user_in, hashed_pw)
    return user_out


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin):
    user_dict = await user_repo.get_by_username(credentials.username)
    if not user_dict or not verify_password(credentials.password, user_dict.get("hashed_password", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    access_token = create_access_token({"sub": credentials.username})
    user_out = UserOut(**user_dict)
    return Token(access_token=access_token, token_type="bearer", user=user_out)


@router.get("/me", response_model=UserOut)
async def get_me(current_user: UserOut = Depends(get_current_user)):
    return current_user
