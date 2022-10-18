from app.db.repositories.base import BaseRepository
from app.models.user import UserCreate, UserUpdate, UserInDB


CREATE_USER_QUERY = """
    INSERT INTO users (email, password_hash)
    VALUES (:email, :password_hash)
    RETURNING id, email, email_verified;
"""


class UsersRepository(BaseRepository):
    """"
    All database actions associated with the User resource
    """

    async def create_user(self, *, new_user: UserCreate) -> UserInDB:
        query_values = {
			'email': new_user.email,
			'password_hash': new_user.password
			}
        user = await self.db.fetch_one(query=CREATE_USER_QUERY, values=query_values)

        return UserInDB(**user)


