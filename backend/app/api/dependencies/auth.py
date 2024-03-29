from typing import Optional
import logging

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.config import SECRET_KEY, API_PREFIX
from app.models.user import UserInDB
from app.api.dependencies.database import get_repository
from app.db.repositories.users import UsersRepository
from app.services import auth_service


oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{API_PREFIX}/users/login/token/")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl=f"{API_PREFIX}/users/login/token/", auto_error=False)

async def get_user_from_token(
    *,
    token: str = Depends(oauth2_scheme),
    user_repo: UsersRepository = Depends(get_repository(UsersRepository)),
    token_type: str = 'bearer'
) -> Optional[UserInDB]:
    try:
        userid = auth_service.get_userid_from_token(
                token=token, 
                secret_key=str(SECRET_KEY),
                token_type=token_type,)
        user = await user_repo.get_user_by_id(userid=userid)
    except Exception as e:
        logging.exception(e)
        raise e

    return user

async def get_user_from_token_optional(
    *,
    token: Optional[str] = Depends(oauth2_scheme_optional),
    user_repo: UsersRepository = Depends(get_repository(UsersRepository)),
    token_type: str = 'bearer'
) -> Optional[UserInDB]:
    user = None
    if token:
        try:
            userid = auth_service.get_userid_from_token(
                    token=token, 
                    secret_key=str(SECRET_KEY),
                    token_type=token_type,)
            user = await user_repo.get_user_by_id(userid=userid)
        except Exception as e:
            logging.exception(e)

        return user



def get_current_active_user(
    token_type: str = 'bearer',
    current_user: UserInDB = Depends(get_user_from_token)) -> Optional[UserInDB]:
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="No authenticated user.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return current_user

def get_current_optional_user(
    token_type: str = 'bearer',
    current_user: Optional[UserInDB] = Depends(get_user_from_token_optional)) -> Optional[UserInDB]:

    return current_user

