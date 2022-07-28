"""
Cit Clientes Registros v2, esquemas de pydantic
"""
from datetime import date, datetime
from pydantic import BaseModel


class CitClienteRegistroOut(BaseModel):
    """Esquema para entregar registros de clientes"""

    id: int
    nombres: str
    apellido_primero: str
    apellido_segundo: str
    curp: str
    telefono: str
    email: str
    expiracion: datetime
    cadena_validar: str
    mensajes_cantidad: int
    ya_registrado: bool

    class Config:
        """SQLAlchemy config"""

        orm_mode = True


class CitClienteRegistroCantidadesCreadasPorDiaOut(BaseModel):
    """Esquema para entregar cantidades de citas creadas por día"""

    creado: date
    cantidad: int
