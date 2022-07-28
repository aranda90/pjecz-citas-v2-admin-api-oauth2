"""
Cit Clientes v2, CRUD (create, read, update, and delete)
"""
from datetime import date, timedelta
from typing import Any
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from lib.exceptions import IsDeletedException, NotExistsException, OutOfRangeException

from .models import CitCliente

HOY = date.today()
ANTIGUA_FECHA = date(year=2022, month=1, day=1)


def get_cit_clientes(db: Session) -> Any:
    """Consultar los clientes activos"""
    return db.query(CitCliente).filter_by(estatus="A").order_by(CitCliente.id.desc())


def get_cit_cliente(db: Session, cit_cliente_id: int) -> CitCliente:
    """Consultar un cliente por su id"""
    cit_cliente = db.query(CitCliente).get(cit_cliente_id)
    if cit_cliente is None:
        raise NotExistsException("No existe ese cliente")
    if cit_cliente.estatus != "A":
        raise IsDeletedException("No es activo ese cliente, está eliminado")
    return cit_cliente


def get_cit_clientes_cantidades_creados_por_dia(
    db: Session,
    creado: date = None,
    creado_desde: date = None,
    creado_hasta: date = None,
) -> Any:
    """Calcular las cantidades de clientes creados por dia"""
    # Observe que para la columna creado se usa la función func.date()
    consulta = db.query(
        func.date(CitCliente.creado).label("creado"),
        func.count(CitCliente.id).label("cantidad"),
    )
    # Si se recibe creado, se limita a esa fecha
    if creado:
        if not ANTIGUA_FECHA <= creado <= HOY:
            raise OutOfRangeException("Creado fuera de rango")
        consulta = consulta.filter(func.date(CitCliente.creado) == creado)
    else:
        # Si se reciben creado_desde y creado_hasta, validar que sean correctos
        if creado_desde and creado_hasta:
            if creado_desde > creado_hasta:
                raise OutOfRangeException("El rango de fechas no es correcto")
        # Si NO se reciben creado_desde y creado_hasta, se limitan a los últimos 30 días
        if creado_desde is None and creado_hasta is None:
            creado_desde = HOY - timedelta(days=30)
            creado_hasta = HOY
        # Si solo se recibe creado_desde, entonces creado_hasta es HOY
        if creado_desde and creado_hasta is None:
            creado_hasta = HOY
        if creado_desde:
            if not ANTIGUA_FECHA <= creado_desde <= HOY:
                raise OutOfRangeException("Creado desde fuera de rango")
            consulta = consulta.filter(func.date(CitCliente.creado) >= creado_desde)
        if creado_hasta:
            if not ANTIGUA_FECHA <= creado_hasta <= HOY:
                raise OutOfRangeException("Creado hasta fuera de rango")
            consulta = consulta.filter(func.date(CitCliente.creado) <= creado_hasta)
    return consulta.group_by(func.date(CitCliente.creado))
