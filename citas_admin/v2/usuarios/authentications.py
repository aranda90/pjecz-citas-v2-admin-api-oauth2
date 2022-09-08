"""
Autentificaciones
"""
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from config.settings import SECRET_KEY, ALGORITHM
from lib.database import get_db
from .models import Usuario
from .schemas import TokenData, UsuarioInDB

pwd_context = CryptContext(schemes=["pbkdf2_sha256", "des_crypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Validar contraseña"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Cifrar contraseña"""
    return pwd_context.hash(password)


def get_user(username: str, db: Session = Depends(get_db)) -> Optional[UsuarioInDB]:
    """Obtener el usuario a partir de su e-mail"""
    usuario = db.query(Usuario).filter(Usuario.email == username).first()
    if usuario:
        datos = {
            "id": usuario.id,
            "distrito_id": usuario.autoridad.distrito_id,
            "distrito_nombre": usuario.autoridad.distrito.nombre,
            "distrito_nombre_corto": usuario.autoridad.distrito.nombre_corto,
            "autoridad_id": usuario.autoridad_id,
            "autoridad_clave": usuario.autoridad.clave,
            "autoridad_descripcion": usuario.autoridad.descripcion,
            "autoridad_descripcion_corta": usuario.autoridad.descripcion_corta,
            "oficina_id": usuario.oficina_id,
            "oficina_clave": usuario.oficina.clave,
            "oficina_descripcion": usuario.oficina.descripcion,
            "oficina_descripcion_corta": usuario.oficina.descripcion_corta,
            "email": usuario.email,
            "nombres": usuario.nombres,
            "apellido_paterno": usuario.apellido_paterno,
            "apellido_materno": usuario.apellido_materno,
            "curp": usuario.curp,
            "puesto": usuario.puesto,
            "telefono_celular": usuario.telefono_celular,
            "username": usuario.email,
            "permissions": usuario.permissions,
            "hashed_password": usuario.contrasena,
            "disabled": usuario.estatus != "A",
        }
        return UsuarioInDB(**datos)


def authenticate_user(username: str, password: str, db: Session = Depends(get_db)) -> Optional[UsuarioInDB]:
    """Autentificar el usuario"""
    user = get_user(username, db)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Crear el token de acceso"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> UsuarioInDB:
    """Obtener el usuario a partir del token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError as jwt_error:
        raise credentials_exception from jwt_error
    usuario = get_user(token_data.username, db)
    if usuario is None:
        raise credentials_exception
    return usuario


async def get_current_active_user(current_user: UsuarioInDB = Depends(get_current_user)) -> UsuarioInDB:
    """Obtener el usuario a partir del token y provocar error si está inactivo"""
    if current_user.disabled:
        raise HTTPException(status_code=401, detail="Unauthorized (usuario inactivo)")
    return current_user
