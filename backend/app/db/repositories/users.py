from pydantic import EmailStr
from typing import Optional

from fastapi import HTTPException
from starlette.status import HTTP_400_BAD_REQUEST
from databases import Database

from app.db.repositories.base import BaseRepository
from app.models.user import UserCreate, UserInDB, UserPublic
from app.services import auth_service

from app.db.repositories.profiles import ProfilesRepository
from app.models.profile import ProfileCreate, ProfilePublic

import logging

REGISTER_NEW_USER_QUERY = """
    INSERT INTO users (email, password, salt)
    VALUES (:email, :password, :salt)
    RETURNING id, email, email_verified, password, salt, is_admin;
"""

GET_USER_BY_EMAIL_QUERY = """
    SELECT id, email, email_verified, password, salt, created_at, updated_at, is_admin
    FROM users
    WHERE email = :email;
"""

GET_USER_BY_ID_QUERY = """
    SELECT id, email, email_verified, password, salt, created_at, updated_at, is_admin
    FROM users
    WHERE id = :id;
"""

UPDATE_USER_QUERY = """
    UPDATE users 
    SET email_verified = :email_verified, password = :password, salt = :salt
    WHERE id = :id
    RETURNING id, email, email_verified, password, salt, created_at, updated_at, is_admin;
"""

class UsersRepository(BaseRepository):
    """"
    All database actions associated with the User resource
    """

    def __init__(self, db: Database) -> None:
        super().__init__(db)
        self.auth_service = auth_service
        self.profiles_repo = ProfilesRepository(db)

    async def get_user_by_email(self, *, email: EmailStr, populate: bool = True) -> UserInDB:
        user_record = await self.db.fetch_one(query=GET_USER_BY_EMAIL_QUERY, values={"email": email})
        if user_record:
            user = UserInDB(**user_record)
            if populate:
                return await self.populate_user(user=user)
            return user

    async def update_user(self, *, user: UserInDB, update_params: dict) -> UserInDB:
        update_user_params = user.copy(update=update_params, 
                exclude={"email", "created_at", "updated_at", "access_token", "profile"})
        updated_user = await self.db.fetch_one(query=UPDATE_USER_QUERY, values=update_user_params.dict())
        return UserInDB(**updated_user)

    async def verify_user_email(self, *, userid: int):
        user = await self.get_user_by_id(userid=userid, populate=False)
        if not user or user.email_verified:
            return None
        return await self.update_user(user=user, update_params={'email_verified': True})

    async def change_user_password(self, 
            *, 
            userid: int,
            password: str,
            ) -> UserInDB:
        user = await self.get_user_by_id(userid=userid, populate=False)
        if not user:
            return None
        user_password_update = self.auth_service.create_salt_and_hashed_password(
            plaintext_password=password)
        return await self.update_user(user=user, update_params=user_password_update.dict())

    async def get_user_by_id(self, *, userid: int, populate: bool = True) -> UserInDB:
        user_record = await self.db.fetch_one(query=GET_USER_BY_ID_QUERY, values={"id": userid})
        if user_record:
            user = UserInDB(**user_record)
            if populate:
                return await self.populate_user(user=user)                
            return user

    async def register_new_user(self, *, new_user: UserCreate) -> UserInDB:
        # make sure email isn't already taken
        if await self.get_user_by_email(email=new_user.email):
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail="That email is already taken. Login with that email or register with another one."
            )
        
        user_password_update = self.auth_service.create_salt_and_hashed_password(
            plaintext_password=new_user.password)
        new_user_params = new_user.copy(update=user_password_update.dict())
        created_user = await self.db.fetch_one(query=REGISTER_NEW_USER_QUERY, values=new_user_params.dict())
        await self.profiles_repo.create_profile_for_user(
            profile_create=ProfileCreate(user_id=created_user["id"]))        
        return await self.populate_user(user=UserInDB(**created_user))

    async def authenticate_user(self, *, email: EmailStr, password: str) -> Optional[UserInDB]:
        # make user user exists in db
        user = await self.get_user_by_email(email=email, populate=False)
        if not user:
            return None
        # if submitted password doesn't match
        if not self.auth_service.verify_password(password=password, salt=user.salt, hashed_pw=user.password):
            return None
        return user

    async def populate_user(self, *, user: UserInDB) -> UserInDB:
        return UserPublic(
            # unpack the user in db dict into the UserPublic model
            # which will remove "password" and "salt"
            **user.dict(),
            # fetch the user's profile from the profiles repo
            profile=await self.profiles_repo.get_profile_by_user_id(user_id=user.id)
        )

