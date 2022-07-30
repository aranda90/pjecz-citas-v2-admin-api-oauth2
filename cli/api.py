"""
CLI API
"""
import os

from dotenv import load_dotenv
import requests

import exceptions

load_dotenv()
HOST = os.getenv("HOST", "")  # http://127.0.0.1:8006
USERNAME = os.getenv("USERNAME", "")
PASSWORD = os.getenv("PASSWORD", "")


def authorization() -> dict:
    """Autentificarse"""
    if HOST == "":
        raise exceptions.CLIConfigurationError("No se ha definido el host")
    if USERNAME == "":
        raise exceptions.CLIConfigurationError("No se ha definido el usuario")
    if PASSWORD == "":
        raise exceptions.CLIConfigurationError("No se ha definido la contraseña")
    data = {"username": USERNAME, "password": PASSWORD}
    headers = {"content-type": "application/x-www-form-urlencoded"}
    try:
        response = requests.post(f"{HOST}/token", data=data, headers=headers)
    except requests.exceptions.RequestException as error:
        raise exceptions.CLIConnectionError("No hay respuesta al tratar de autentificar") from error
    if response.status_code != 200:
        raise exceptions.CLIStatusCodeError(f"No es lo esperado el status code: {response.status_code}")
    data_json = response.json()
    if not "access_token" in data_json:
        raise exceptions.CLIAuthenticationError("No se recibio el access_token en la respuesta")
    authorization_header = {"Authorization": "Bearer " + data_json["access_token"]}
    return authorization_header


def base_url() -> str:
    """URL base de la API"""
    if HOST == "":
        raise exceptions.CLIConfigurationError("No se ha definido el host")
    return f"{HOST}/v2"
