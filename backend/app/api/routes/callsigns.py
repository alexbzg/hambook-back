from typing import List

from pydantic import constr
from fastapi import APIRouter, HTTPException
from starlette.status import HTTP_404_NOT_FOUND

from app.services import callsigns_autocomplete_service

router = APIRouter()

@router.get("/autocomplete/{start}", response_model=List[str], name="callsigns:autocomplete")
async def callsigns_autocomplete(*, 
    start: constr(to_upper=True),
    count: int = 20) -> List[str]:
    suggestions = []
    try:
        for callsign in callsigns_autocomplete_service.find_all(start):
            suggestions.append(callsign[0])
            if len(suggestions) == count:
                break
    except StopIteration:
        pass

    if not suggestions:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="Callsigns not found"
        )

    return suggestions



 