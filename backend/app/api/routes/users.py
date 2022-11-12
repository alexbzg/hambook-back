from fastapi import Depends, APIRouter, HTTPException, Path, Body
from fastapi.responses import HTMLResponse
from starlette.status import (
    HTTP_200_OK, 
    HTTP_201_CREATED, 
    HTTP_400_BAD_REQUEST, 
    HTTP_401_UNAUTHORIZED, 
    HTTP_404_NOT_FOUND, 
    HTTP_422_UNPROCESSABLE_ENTITY,
)
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import EmailStr, constr

from app.api.dependencies.database import get_repository
from app.api.dependencies.auth import get_current_active_user, get_user_from_token
from app.models.user import UserCreate, UserInDB, UserPublic, UserPasswordReset
from app.models.token import AccessToken
from app.services import auth_service, email_service, html_templates_service
from app.db.repositories.users import UsersRepository
from app.core.config import SRV_URI, API_PREFIX, TEMPORARY_TOKEN_EXPIRE_MINUTES

router = APIRouter()
API_URI = f"{SRV_URI}{API_PREFIX}"

@router.post("/", response_model=UserPublic, name="users:register-new-user", status_code=HTTP_201_CREATED)
async def register_new_user(
    new_user: UserCreate = Body(..., embed=True),
    user_repo: UsersRepository = Depends(get_repository(UsersRepository)),
) -> UserPublic:
    created_user = await user_repo.register_new_user(new_user=new_user)

    await send_email_verification(user=created_user)

    return get_user_public(created_user)

def get_user_public(user: UserInDB) -> UserPublic:
    access_token = AccessToken(
        access_token=auth_service.create_access_token_for_user(user=user), token_type="bearer"
    )
    return UserPublic(**user.dict(exclude={'access_token'}), access_token=access_token)

@router.post("/login/token/", response_model=AccessToken, name="users:login-email-and-password")
async def user_login_with_email_and_password(
    user_repo: UsersRepository = Depends(get_repository(UsersRepository)),
    form_data: OAuth2PasswordRequestForm = Depends(OAuth2PasswordRequestForm),
) -> AccessToken:
    user = await user_repo.authenticate_user(email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Authentication was unsuccessful.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = AccessToken(access_token=auth_service.create_access_token_for_user(user=user),
            token_type="bearer")
    return access_token

@router.get("/me/", response_model=UserPublic, name="users:get-current-user")
async def get_currently_authenticated_user(current_user: UserInDB = Depends(get_current_active_user)) -> UserPublic:
    return current_user

@router.get("/email_verification/request", response_model=dict, name="users:email-verification-request")
async def email_verification_request(current_user: UserInDB = Depends(get_current_active_user)) -> dict:
    await send_email_verification(user=current_user)

    return {'result': 'Ok'}

@router.get("/email_verification/{token}", name="users:email-verification")
async def email_verification(
        token: str, 
        user_repo: UsersRepository = Depends(get_repository(UsersRepository)),
        ) -> UserInDB:
    try:
        userid = auth_service.get_userid_from_token(token=token, token_type='email verification',)
    except HTTPException:
        userid = None

    status_code = HTTP_200_OK
    result = 'Your email was verified successfully.'
    if (userid):
        user = await user_repo.verify_user_email(userid=userid)


    if (not userid or not user):
        status_code=HTTP_401_UNAUTHORIZED
        result = 'Invalid verification code or email is already verified'

    template = html_templates_service.template('email_verification_response')
    html = template.render(title='HAMBOOK.net email verification', result=result)

    return HTMLResponse(content=html, status_code=status_code)

async def send_email_verification(user: UserInDB):
    if (user.email_verified):
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST, 
            detail='The email is already verified',
        )
    verification_token = auth_service.create_access_token_for_user(
        user=user, 
        token_type='email verification',
        expires_in=TEMPORARY_TOKEN_EXPIRE_MINUTES
        )
    subject = 'Hambook.net email verification'
    await email_service.send(
            recipients=[EmailStr(user.email)],
            subject=subject,
            template='email_verification',
            template_params={
                'verify_url': f"{API_URI}/users/email_verification/{verification_token}",
                'title': subject})


@router.get("/password_reset/request/{email}", response_model=dict, name="users:password-reset-request")
async def password_reset_request(
        email: EmailStr, 
        user_repo: UsersRepository = Depends(get_repository(UsersRepository)),
        ) -> dict:
    user = await user_repo.get_user_by_email(email=email)
    if not user:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST, 
            detail='No user was found with this email',
        )
    token = auth_service.create_access_token_for_user(
            user=user, 
            token_type='password reset',
            expires_in=TEMPORARY_TOKEN_EXPIRE_MINUTES,
            )
    subject = 'Hambook.net password reset'
    await email_service.send(
            recipients=[EmailStr(email)],
            subject=subject,
            template='password_reset',
            template_params={
                'reset_url': f"{SRV_URI}/password_reset?token={token}",
                'title': subject})
   
    return {'result': 'Ok'}

@router.post("/password_reset", response_model=UserPublic, name="users:password-reset")
async def password_reset(
    password_reset: UserPasswordReset = Body(..., embed=True),
    user_repo: UsersRepository = Depends(get_repository(UsersRepository)),
    )->UserPublic:
    
    try:
        userid = auth_service.get_userid_from_token(token=password_reset.token, token_type='password reset',)
    except HTTPException:
        userid = None

    if (userid):
        user = await user_repo.change_user_password(userid=userid, password=password_reset.password)

    if (not userid or not user):
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED, 
            detail='Invalid reset code',
        )

    #if the user had not verified email already we will do it now because they just has passed
    #similar requirements
    if not user.email_verified:
        user = await user_repo.verify_user_email(userid=userid)

    return get_user_public(user)
    

