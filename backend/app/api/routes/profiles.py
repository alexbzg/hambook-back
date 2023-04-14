from fastapi import Depends, APIRouter, HTTPException, Path, Body, status
from pydantic import constr

from app.api.dependencies.auth import get_current_active_user
from app.api.dependencies.database import get_repository
from app.models.user import UserCreate, UserInDB, UserPublic
from app.models.core import Callsign, CallsignModel
from app.models.profile import ProfileUpdate, ProfilePublic
from app.db.repositories.profiles import ProfilesRepository

import logging

router = APIRouter()

@router.get("/{user_id:int}/", response_model=ProfilePublic, name="profiles:get-profile-by-user_id")
async def get_profile_by_user_id(*, 
	user_id: int, 
	profiles_repo: ProfilesRepository = Depends(get_repository(ProfilesRepository), )) -> ProfilePublic:
	profile = await profiles_repo.get_profile_by_user_id(user_id=user_id)
	if not profile:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No profile found with that user_id.")
	return profile    

@router.get("/{callsign:str}/", response_model=ProfilePublic, name="profiles:get-profile-by-callsign")
async def get_profile_by_callsign(*, 
    callsign: Callsign,
	profiles_repo: ProfilesRepository = Depends(get_repository(ProfilesRepository))) -> ProfilePublic:
	callsign = callsign.upper()
	profile = await profiles_repo.get_profile_by_callsign(callsign=callsign)
	if not profile:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No profile found with that callsign.")
	return profile    

@router.put("/me/", response_model=ProfilePublic, name="profiles:update-own-profile")
async def update_own_profile(
	profile_update: ProfileUpdate = Body(..., embed=True),
	current_user: UserInDB = Depends(get_current_active_user),
	profiles_repo: ProfilesRepository = Depends(get_repository(ProfilesRepository)),    
) -> ProfilePublic:
	updated_profile = await profiles_repo.update_profile(profile_update=profile_update, requesting_user=current_user)

	return updated_profile

@router.get("/search/{expression}", response_model=list[ProfilePublic], name="profiles:search")
async def password_reset_request(
    expression: constr(strip_whitespace=True, min_length=3), 
    profiles_repo: ProfilesRepository = Depends(get_repository(ProfilesRepository)),
    ) -> list[ProfilePublic]:
    
    callsign = first_name = last_name = None
    search_results = None
    try:
        callsign = CallsignModel(callsign=expression).callsign
    except ValueError:
        pass

    if not callsign:
        if ' ' in expression:
            first_name, last_name = expression.split()[0:2]
        else:
            first_name = last_name = expression
           
    search_results = await profiles_repo.find_profiles_by_callsign_or_name(
            callsign=callsign, first_name=first_name, last_name=last_name)

    if not search_results:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
            detail="Profiles not found.")

    return search_results





