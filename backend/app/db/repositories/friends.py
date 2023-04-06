from app.db.repositories.base import BaseRepository
from app.models.user import UserInDB
from app.models.friend import FriendBase, FriendInDB, FriendPublic
import logging

ADD_FRIEND_QUERY = """
    INSERT INTO friends (user_id, friend_id)
    VALUES (:user_id, :friend_id)
    RETURNING id, user_id, friend_id, created_at;
"""

DELETE_FRIEND_QUERY = """
    DELETE from friends 
    WHERE user_id = :user_id and friend_id = :friend_id;
"""

class FriendsRepository(BaseRepository):
    async def add_friend(self, *, 
        requesting_user: UserInDB,
        friend_id: int) -> FriendInDB:

        added_friend = await self.db.fetch_one(query=ADD_FRIEND_QUERY, 
                values={'user_id': int(requesting_user.id), 'friend_id': friend_id})

        return FriendInDB(**added_friend)

    async def delete_friend(self, *, 
        requesting_user: UserInDB,
        friend_id: int) -> None:
            await self.db.execute(query=DELETE_FRIEND_QUERY, 
                    values={'user_id': int(requesting_user.id), 'friend_id': friend_id})
