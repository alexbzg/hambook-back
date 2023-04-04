from databases import Database

from app.db.repositories.base import BaseRepository
from app.db.repositories.media import MediaRepository, mediaPublicFromDB
from app.models.profile import ProfileCreate, ProfileUpdate, ProfileInDB, ProfilePublic
from app.models.user import UserInDB
from app.models.media import MediaType


CREATE_PROFILE_FOR_USER_QUERY = """
    INSERT INTO profiles (first_name, last_name, country, region, district, 
        city, zip_code, address, phone, current_callsign, prev_callsigns,birthdate, bio, user_id)
    VALUES (:first_name, :last_name, :country, :region, :city, :district, :zip_code, :address, :phone, 
        :current_callsign, :prev_callsigns, :birthdate, :bio, :user_id)
    RETURNING id, first_name, last_name, country, region, district, city, zip_code, address, 
        default_image, current_callsign, prev_callsigns, birthdate, bio, user_id, 
        created_at, updated_at;
"""

GET_PROFILE_BY_USER_ID_QUERY = """
    SELECT id, first_name, last_name, country, region, district, city, zip_code, address, phone, 
        current_callsign, prev_callsigns, birthdate, bio, user_id, created_at, updated_at
    FROM profiles
    WHERE user_id = :user_id;
"""

GET_PROFILE_BY_CALLSIGN_QUERY = """
    SELECT id, first_name, last_name, country, region, district, city, zip_code, address, phone, 
        current_callsign, prev_callsigns, birthdate, bio, user_id, created_at, updated_at
    FROM profiles
    WHERE current_callsign = :callsign;
"""

UPDATE_PROFILE_QUERY = """
    UPDATE profiles
    SET 
        first_name          = :first_name,
        last_name           = :last_name, 
        country             = :country, 
        region              = :region, 
        district            = :district,
        city                = :city, 
        zip_code            = :zip_code,
		address				= :address,
        phone               = :phone,
		default_image 		= :default_image, 
		current_callsign	= :current_callsign,
		prev_callsigns		= :prev_callsigns,
		birthdate			= :birthdate,
		bio					= :bio 
    WHERE user_id = :user_id
    RETURNING id, first_name, last_name, country, region, district, city, zip_code, address, phone, 
        default_image, current_callsign, prev_callsigns, birthdate, bio, user_id, 
        created_at, updated_at;
"""

class ProfilesRepository(BaseRepository):

    def __init__(self, db: Database) -> None:
        super().__init__(db)
        self.media_repo = MediaRepository(db)

    async def create_profile_for_user(self, *, profile_create: ProfileCreate) -> ProfilePublic:
        created_profile = await self.db.fetch_one(query=CREATE_PROFILE_FOR_USER_QUERY, values=profile_create.dict())

        return await self.populate_profile(profile=ProfileInDB(**created_profile))

    async def get_profile_by_user_id(self, *, user_id: int, populate: bool = True) -> ProfilePublic:
        profile_record = await self.db.fetch_one(query=GET_PROFILE_BY_USER_ID_QUERY, values={"user_id": int(user_id)})

        if not profile_record:
            return None

        if populate:
            return await self.populate_profile(profile=ProfileInDB(**profile_record))

        return ProfileInDB(**profile_record)

    async def get_profile_by_callsign(self, *, callsign: str, populate: bool = True) -> ProfilePublic:
        profile_record = await self.db.fetch_one(query=GET_PROFILE_BY_CALLSIGN_QUERY, values={"callsign": callsign})

        if not profile_record:
            return None

        return await self.populate_profile(profile=ProfileInDB(**profile_record))

    async def update_profile(self, *, 
            profile_update: ProfileUpdate, 
            requesting_user: UserInDB, 
            populate: bool = True) -> ProfilePublic:

        profile = await self.get_profile_by_user_id(user_id=requesting_user.id, populate=False)
        update_params = profile.copy(update=profile_update.dict(exclude_unset=True))
        updated_profile = await self.db.fetch_one(
            query=UPDATE_PROFILE_QUERY,
            values=update_params.dict(exclude={"id", "created_at", "updated_at"}),
        )
        return await self.populate_profile(profile=ProfileInDB(**updated_profile))


    async def populate_profile(self, *, profile: ProfileInDB) -> ProfilePublic:

        avatar_record = await self.media_repo.get_user_avatar(user_id=profile.user_id)
        avatar = mediaPublicFromDB(avatar_record) if avatar_record else None
        profile_media_records = await self.media_repo.get_media_by_user_id_media_type(user_id=profile.user_id,
                media_type=MediaType.profile_media)
        profile_media = [mediaPublicFromDB(media) for media in profile_media_records] if profile_media_records else []

        return ProfilePublic(**profile.dict(), avatar=avatar, media=profile_media)
