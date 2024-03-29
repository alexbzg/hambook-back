from typing import List

from databases import Database

from app.db.repositories.base import BaseRepository
from app.db.repositories.media import MediaRepository

from app.models.post import PostUpdate, PostInDB, PostPublic, PostVisibility
from app.models.user import UserInDB

CREATE_POST_QUERY = """
    INSERT INTO posts (post_type, visibility, title,  contents, user_id)
    VALUES (:post_type, :visibility, :title,  :contents, :user_id)
    RETURNING id, post_type, visibility, title,  contents, user_id, created_at, updated_at;
"""

UPDATE_POST_QUERY = """
    UPDATE posts
    set 
        post_type       = :post_type, 
        visibility      = :visibility,
        title           = :title,
        contents        = :contents
    WHERE id = :id
    RETURNING id, post_type, visibility, title,  contents, user_id, created_at, updated_at;
"""


DELETE_POST_QUERY = """
    DELETE from posts
    WHERE id = :id;
"""

GET_POSTS_BY_USER_ID_QUERY = """
    SELECT 
        id, post_type, visibility, title,  contents, user_id, created_at, updated_at
    FROM posts
    WHERE user_id = :user_id and visibility >= :visibility
    order by id desc;
"""

GET_SITE_POSTS_QUERY = """
    SELECT 
        id, post_type, visibility, title,  contents, user_id, created_at, updated_at
    FROM posts
    WHERE post_type = 1 and visibility >= :visibility
    order by id desc;
"""

GET_POST_BY_ID_QUERY = """
    SELECT 
        id, post_type, visibility, title,  contents, user_id, created_at, updated_at
    FROM posts
    WHERE id = :id;
"""

class PostsRepository(BaseRepository):

    def __init__(self, db: Database) -> None:
        super().__init__(db)
        self.media_repo = MediaRepository(db)


    async def create_post(self, *, 
        new_post: PostUpdate,
        requesting_user: UserInDB) -> PostInDB:

        created_post = await self.db.fetch_one(query=CREATE_POST_QUERY, 
                values={**new_post.dict(exclude={"post_images", "deleted_images"}), 
                    "user_id": int(requesting_user.id)})

        return PostInDB(**created_post)

    async def get_posts_by_user_id(self, *, 
        user_id: int,
        visibility: PostVisibility = PostVisibility.private) -> List[PostInDB]:
        posts = await self.db.fetch_all(query=GET_POSTS_BY_USER_ID_QUERY, 
                values={"user_id": user_id, 'visibility': visibility})

        if not posts:
            return None

        return [PostInDB(**post) for post in posts]

    async def get_site_posts(self, *, 
        visibility: PostVisibility = PostVisibility.private) -> List[PostInDB]:
        posts = await self.db.fetch_all(query=GET_SITE_POSTS_QUERY, 
                values={'visibility': visibility})

        if not posts:
            return None

        return [PostInDB(**post) for post in posts]


    async def get_post_by_id(self, *, id: int) -> PostInDB:
        post = await self.db.fetch_one(query=GET_POST_BY_ID_QUERY, values={"id": id})

        if not post:
            return None

        return PostInDB(**post, images=await self.media_repo.get_media_by_post_id(post_id=id))

    async def update_post(self, *, post: PostInDB, post_update: PostUpdate) -> PostInDB:

        update_params = post.copy(update=post_update.dict(exclude_unset=True))
        updated_post = await self.db.fetch_one(
            query=UPDATE_POST_QUERY,
            values=update_params.dict(
                exclude={"user_id", "created_at", "updated_at", "post_images", "deleted_images", "images"}),
        )

        return PostInDB(**updated_post)


    async def delete_post(self, *, id: int) -> None:
        await self.db.execute(query=DELETE_POST_QUERY, values={"id": id})

