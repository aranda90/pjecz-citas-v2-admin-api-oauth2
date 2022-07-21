"""
Citas V2 Admin API OAuth2
"""
from datetime import timedelta

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_pagination import add_pagination
from sqlalchemy.orm import Session

from config.settings import ACCESS_TOKEN_EXPIRE_MINUTES
from lib.database import get_db

from .v2.distritos.paths import distritos
from .v2.materias.paths import materias

from .v2.usuarios.authentications import authenticate_user, create_access_token, get_current_active_user
from .v2.usuarios.schemas import Token, UsuarioInDB

app = FastAPI(
    title="Citas V2 Admin API OAuth2",
    description="API OAuth2 del sistema de citas para brindar informacion a otros sistemas.",
)

app.include_router(distritos)
app.include_router(materias)

add_pagination(app)


@app.get("/")
async def root():
    """Mensaje de Bienvenida"""
    return {"message": "Bienvenido a Citas v2 admin API OAuth2 del Poder Judicial del Estado de Coahuila de Zaragoza."}


@app.post("/token", response_model=Token)
async def ingresar_para_solicitar_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Entregar el token como un JSON"""
    usuario = authenticate_user(form_data.username, form_data.password, db)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": usuario.username}, expires_delta=access_token_expires)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "username": usuario.username,
    }


@app.get("/profile", response_model=UsuarioInDB)
async def mi_perfil(current_user: UsuarioInDB = Depends(get_current_active_user)):
    """Mostrar el perfil del usuario"""
    return current_user
