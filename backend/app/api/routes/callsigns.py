from typing import List

from pydantic import constr
from fastapi import APIRouter, HTTPException, Depends
from starlette.status import HTTP_404_NOT_FOUND

from app.services import callsigns_autocomplete_service
from app.services import qrz_client_service
from app.api.dependencies.auth import get_current_active_user
from app.models.core import Callsign
from app.models.user import UserInDB

router = APIRouter()

@router.get("/autocomplete/{start}", response_model=List[str], name="callsigns:autocomplete")
async def callsigns_autocomplete(*, 
    start: constr(to_upper=True),
    limit: int = 20) -> List[str]:
    suggestions = []
    try:
        for callsign in callsigns_autocomplete_service.find_all(start):
            suggestions.append(callsign[0])
            if len(suggestions) == limit:
                break
    except StopIteration:
        pass

    if not suggestions:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="Callsigns not found"
        )

    return suggestions


@router.get("/qrz/{callsign}", response_model=dict, name="callsigns:qrz-lookup")
async def callsigns_qrz_lookup(*, 
	current_user: UserInDB = Depends(get_current_active_user),
    callsign: Callsign) -> dict:

    lookup_data = await qrz_client_service.lookup(callsign.lower())

    if not lookup_data:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="Callsign not found"
        )

    return lookup_data


 
