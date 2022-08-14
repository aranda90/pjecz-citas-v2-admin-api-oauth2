"""
Cit Dias Disponibles CRUD (create, read, update, and delete)
"""
from typing import Any
import requests

import lib.exceptions


def get_cit_dias_disponibles(
    base_url: str,
    authorization_header: dict,
    limit: int = 40,
) -> Any:
    """Solicitar dias disponibles, entrega un listado de fechas"""
    parametros = {"limit": limit}
    try:
        response = requests.get(
            f"{base_url}/cit_dias_disponibles",
            headers=authorization_header,
            params=parametros,
            timeout=12,
        )
    except requests.exceptions.RequestException as error:
        raise lib.exceptions.CLIConnectionError("No hay respuesta al solicitar dias disponibles") from error
    if response.status_code != 200:
        raise lib.exceptions.CLIStatusCodeError(f"No es lo esperado el status code: {response.status_code} al solicitar dias disponibles\nmensaje: {response.text}")
    data_json = response.json()
    # if "items" not in data_json or "total" not in data_json:
    #    raise lib.exceptions.CLIResponseError("No se recibio items o total en la respuesta al solicitar dias disponibles")
    return data_json


def get_cit_dia_disponible(
    base_url: str,
    authorization_header: dict,
) -> Any:
    """Solicitar el proximo dia disponible, por ejemplo, si hoy es viernes y el lunes es dia inhabil, entrega el martes"""
    try:
        response = requests.get(
            f"{base_url}/cit_dias_disponibles/proximo",
            headers=authorization_header,
            timeout=12,
        )
    except requests.exceptions.RequestException as error:
        raise lib.exceptions.CLIConnectionError("No hay respuesta al solicitar dias disponibles") from error
    if response.status_code != 200:
        raise lib.exceptions.CLIStatusCodeError(f"No es lo esperado el status code: {response.status_code} al solicitar dias disponibles\nmensaje: {response.text}")
    data_json = response.json()
    if "fecha" not in data_json:
        raise lib.exceptions.CLIResponseError("No se recibio la fecha en la respuesta al solicitar dias disponibles")
    return data_json
