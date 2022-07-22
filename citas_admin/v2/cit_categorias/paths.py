"""
Cit Categorias v2, rutas (paths)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.orm import Session

from lib.database import get_db
from lib.exceptions import IsDeletedException, NotExistsException
from lib.fastapi_pagination import LimitOffsetPage

from .crud import get_cit_categorias, get_cit_categoria
from .schemas import CitCategoriaOut
from ..permisos.models import Permiso
from ..usuarios.authentications import get_current_active_user
from ..usuarios.schemas import UsuarioInDB

cit_categorias = APIRouter(prefix="/v2/cit_categorias", tags=["citas"])


@cit_categorias.get("", response_model=LimitOffsetPage[CitCategoriaOut])
async def listado_cit_categorias(
    current_user: UsuarioInDB = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Listado de categorias"""
    if "CIT CATEGORIAS" not in current_user.permissions or current_user.permissions["CIT CATEGORIAS"] < Permiso.VER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    try:
        listado = get_cit_categorias(db)
    except (IsDeletedException, NotExistsException) as error:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail=f"Not acceptable: {str(error)}") from error
    return paginate(listado)


@cit_categorias.get("/{cit_categoria_id}", response_model=CitCategoriaOut)
async def detalle_cit_categoria(
    cit_categoria_id: int,
    current_user: UsuarioInDB = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Detalle de una categorias a partir de su id"""
    if "CIT CATEGORIAS" not in current_user.permissions or current_user.permissions["CIT CATEGORIAS"] < Permiso.VER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    try:
        cit_categoria = get_cit_categoria(db, cit_categoria_id=cit_categoria_id)
    except (IsDeletedException, NotExistsException) as error:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail=f"Not acceptable: {str(error)}") from error
    return CitCategoriaOut.from_orm(cit_categoria)