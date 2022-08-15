"""
Cit Citas Commands
"""
from datetime import datetime, timedelta
import locale
import os

from dotenv import load_dotenv
import pandas as pd
import rich
import sendgrid
from sendgrid.helpers.mail import Email, To, Content, Mail
from tabulate import tabulate
import typer

import lib.connections
import lib.exceptions

from .crud import get_cit_citas, get_cit_citas_cantidades_creados_por_dia, get_cit_citas_cantidades_agendadas_por_oficina_servicio
from ..cit_dias_disponibles.crud import get_cit_dia_disponible
from ..oficinas.crud import get_oficinas
from ..usuarios.crud import get_usuarios

app = typer.Typer()

locale.setlocale(locale.LC_TIME, "es_MX.utf8")

# Pandas options on how to display dataframes
pd.set_option("display.max_rows", 500)
pd.set_option("display.max_columns", 500)
pd.set_option("display.width", 150)

# SendGrid environment variables
load_dotenv()
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
SENDGRID_FROM_EMAIL = os.getenv("SENDGRID_FROM_EMAIL")


@app.command()
def consultar(
    limit: int = 40,
    fecha: str = None,
    email: str = None,
    oficina_clave: str = None,
    estado: str = None,
):
    """Consultar citas"""
    rich.print("Consultar citas...")
    try:
        respuesta = get_cit_citas(
            base_url=lib.connections.base_url(),
            authorization_header=lib.connections.authorization(),
            limit=limit,
            fecha=fecha,
            cit_cliente_email=email,
            oficina_clave=oficina_clave,
            estado=estado,
        )
    except lib.exceptions.CLIAnyError as error:
        typer.secho(str(error), fg=typer.colors.RED)
        raise typer.Exit()
    console = rich.console.Console()
    table = rich.table.Table("id", "creado", "oficina", "inicio", "nombre", "servicio", "estado")
    for registro in respuesta["items"]:
        creado = datetime.strptime(registro["creado"], "%Y-%m-%dT%H:%M:%S.%f")
        inicio = datetime.strptime(registro["inicio"], "%Y-%m-%dT%H:%M:%S")
        table.add_row(
            str(registro["id"]),
            creado.strftime("%Y-%m-%d %H:%M:%S"),
            registro["oficina_clave"],
            inicio.strftime("%Y-%m-%d %H:%M:%S"),
            registro["cit_cliente_nombre"],
            registro["cit_servicio_clave"],
            registro["estado"],
        )
    console.print(table)
    rich.print(f"Total: [green]{respuesta['total']}[/green] citas")


@app.command()
def enviar(
    email: str,
    fecha: str,
    oficina_clave: str,
    estado: str = "PENDIENTE",
    limit: int = 400,
):
    """Enviar mensaje con citas"""
    rich.print("Enviar mensaje con citas...")
    # Validate sendgrid environment variables
    try:
        if SENDGRID_API_KEY is None or SENDGRID_API_KEY == "":
            raise lib.exceptions.CLIConfigurationError("Falta SENDGRID_API_KEY")
        if SENDGRID_FROM_EMAIL is None or SENDGRID_FROM_EMAIL == "":
            raise lib.exceptions.CLIConfigurationError("Falta SENDGRID_FROM_EMAIL")
    except lib.exceptions.CLIAnyError as error:
        typer.secho(str(error), fg=typer.colors.RED)
        raise typer.Exit()
    # Get data
    try:
        respuesta = get_cit_citas(
            base_url=lib.connections.base_url(),
            authorization_header=lib.connections.authorization(),
            limit=limit,
            fecha=fecha,
            oficina_clave=oficina_clave,
            estado=estado,
        )
    except lib.exceptions.CLIAnyError as error:
        typer.secho(str(error), fg=typer.colors.RED)
        raise typer.Exit()
    # Terminate if no data
    if respuesta["total"] == 0:
        typer.secho("No hay citas para enviar", fg=typer.colors.YELLOW)
        raise typer.Exit()
    # Convert data to HTML table
    headers = ["ID", "Hora", "Nombre", "Servicio", "Notas"]
    rows = []
    for item in respuesta["items"]:
        inicio = datetime.strptime(item["inicio"], "%Y-%m-%dT%H:%M:%S")
        rows.append(
            [
                item["id"],
                inicio.strftime("%H:%M"),
                item["cit_cliente_nombre"],
                item["cit_servicio_clave"],
                item["notas"],
            ]
        )
    table_html = tabulate(rows, headers=headers, tablefmt="html")
    # Apply style to table
    table_html = table_html.replace("<table>", '<table border="1" style="width:100%; border: 1px solid black; border-collapse: collapse;">')
    # Add padding to cells
    table_html = table_html.replace('<td style="', '<td style="padding: 4px;')
    table_html = table_html.replace("<td>", '<td style="padding: 4px;">')
    # Create message
    subject = f"Citas de la oficina {oficina_clave} para la fecha {fecha}"
    elaboracion_fecha_hora_str = datetime.now().strftime("%d/%B/%Y %I:%M%p")
    contenidos = []
    contenidos.append("<style> td {border:2px black solid !important} </style>")
    contenidos.append("<h1>PJECZ Citas V2</h1>")
    contenidos.append(f"<h2>{subject}</h2>")
    contenidos.append(table_html)
    contenidos.append(f"<p>Fecha de elaboración: <b>{elaboracion_fecha_hora_str}.</b></p>")
    contenidos.append("<p>ESTE MENSAJE ES ELABORADO POR UN PROGRAMA. FAVOR DE NO RESPONDER.</p>")
    # Send message
    sendgrid_client = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)
    from_email = Email(SENDGRID_FROM_EMAIL)
    to_email = To(email)
    content = Content("text/html", "<br>".join(contenidos))
    mail = Mail(
        from_email=from_email,
        to_emails=to_email,
        subject=subject,
        html_content=content,
    )
    sendgrid_client.client.mail.send.post(request_body=mail.get())
    # Print message
    rich.print(f"Mensaje enviado a [blue]{email}[/blue] con [green]{subject}[/green]")


@app.command()
def mostrar_cantidades_creados_por_dia(
    creado: str = None,
    creado_desde: str = None,
    creado_hasta: str = None,
):
    """Mostrar cantidades de citas creadas por dia"""
    rich.print("Mostrar cantidades de citas creadas por dia...")
    try:
        respuesta = get_cit_citas_cantidades_creados_por_dia(
            base_url=lib.connections.base_url(),
            authorization_header=lib.connections.authorization(),
            creado=creado,
            creado_desde=creado_desde,
            creado_hasta=creado_hasta,
        )
    except lib.exceptions.CLIAnyError as error:
        typer.secho(str(error), fg=typer.colors.RED)
        raise typer.Exit()
    console = rich.console.Console()
    table = rich.table.Table("creado", "cantidad")
    for registro in respuesta["items"]:
        table.add_row(
            registro["creado"],
            str(registro["cantidad"]),
        )
    console.print(table)
    rich.print(f"Total: [green]{respuesta['total']}[/green] citas")


@app.command()
def mostrar_cantidades_agendadas_por_oficina_servicio(
    inicio: str = None,
    inicio_desde: str = None,
    inicio_hasta: str = None,
):
    """Mostrar cantidades de citas agendadas por oficina y servicio"""
    rich.print("Mostrar cantidades de citas agendadas por oficina y servicio...")
    try:
        respuesta = get_cit_citas_cantidades_agendadas_por_oficina_servicio(
            base_url=lib.connections.base_url(),
            authorization_header=lib.connections.authorization(),
            inicio=inicio,
            inicio_desde=inicio_desde,
            inicio_hasta=inicio_hasta,
        )
    except lib.exceptions.CLIAnyError as error:
        typer.secho(str(error), fg=typer.colors.RED)
        raise typer.Exit()
    # Convert items to pandas dataframe
    df = pd.DataFrame(respuesta["items"])
    # Change type of columns to category
    df.oficina = df.oficina.astype("category")
    df.servicio = df.servicio.astype("category")
    # Create a pivot table
    pivot_table = df.pivot_table(
        index="oficina",
        columns="servicio",
        values="cantidad",
        aggfunc="sum",
    )
    # Print the pivot table
    console = rich.console.Console()
    console.print(pivot_table)
    rich.print(f"Total: [green]{respuesta['total']}[/green] citas")


@app.command()
def enviar_informe_diario(
    email: str,
):
    """Enviar informe diario"""
    rich.print("Enviar informe diario...")

    # Validate sendgrid environment variables
    try:
        if SENDGRID_API_KEY is None or SENDGRID_API_KEY == "":
            raise lib.exceptions.CLIConfigurationError("Falta SENDGRID_API_KEY")
        if SENDGRID_FROM_EMAIL is None or SENDGRID_FROM_EMAIL == "":
            raise lib.exceptions.CLIConfigurationError("Falta SENDGRID_FROM_EMAIL")
    except lib.exceptions.CLIAnyError as error:
        typer.secho(str(error), fg=typer.colors.RED)
        raise typer.Exit()

    # Authenticate with API
    try:
        base_url = lib.connections.base_url()
        authorization_header = lib.connections.authorization()
    except lib.exceptions.CLIAnyError as error:
        typer.secho(str(error), fg=typer.colors.RED)
        raise typer.Exit()

    # Today's and yesterday date
    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    # Get data for cantidades de citas agendadas por oficina y servicio
    try:
        respuesta = get_cit_citas_cantidades_agendadas_por_oficina_servicio(
            base_url=base_url,
            authorization_header=authorization_header,
            inicio=today,
        )
    except lib.exceptions.CLIAnyError as error:
        typer.secho(str(error), fg=typer.colors.RED)
        raise typer.Exit()
    # Terminate if no data
    if respuesta["total"] == 0:
        typer.secho("No hay datos para hoy", fg=typer.colors.YELLOW)
        raise typer.Exit()
    # Convert items to pandas dataframe
    df = pd.DataFrame(respuesta["items"])
    # Change type of columns oficina and servicio to category
    df.oficina = df.oficina.astype("category")
    df.servicio = df.servicio.astype("category")
    # Create a pivot table
    pivot_table = df.pivot_table(
        index="oficina",
        columns="servicio",
        values="cantidad",
        aggfunc="sum",
    )
    # Convert pivot table to HTML table
    ccaos_table_html = tabulate(pivot_table, headers="keys", tablefmt="html")
    # Apply style to table
    ccaos_table_html = ccaos_table_html.replace("<table>", '<table border="1" style="width:100%; border: 1px solid black; border-collapse: collapse;">')
    # Add padding to cells
    ccaos_table_html = ccaos_table_html.replace('<td style="', '<td style="padding: 4px;')
    ccaos_table_html = ccaos_table_html.replace("<td>", '<td style="padding: 4px;">')
    # Title
    ccaos_title = f"{respuesta['total']} citas agendadas por oficina y servicio en {today}"

    # Get data for cantidades de citas creadas por dia
    try:
        respuesta = get_cit_citas_cantidades_creados_por_dia(
            base_url=base_url,
            authorization_header=authorization_header,
            creado_hasta=yesterday,
        )
    except lib.exceptions.CLIAnyError as error:
        typer.secho(str(error), fg=typer.colors.RED)
        raise typer.Exit()
    # Convert items to pandas dataframe
    df = pd.DataFrame(respuesta["items"])
    # Change type of columns to category
    df.creado = df.creado.astype("category")
    # Order by creado
    df = df.sort_values(by="creado")
    # Convert dataframe to HTML table
    cccd_table_html = tabulate(df, headers="keys", tablefmt="html")
    # Apply style to table
    cccd_table_html = cccd_table_html.replace("<table>", '<table border="1" style="width:100%; border: 1px solid black; border-collapse: collapse;">')
    # Add padding to cells
    cccd_table_html = cccd_table_html.replace('<td style="', '<td style="padding: 4px;')
    cccd_table_html = cccd_table_html.replace("<td>", '<td style="padding: 4px;">')
    # Title
    cccd_title = f"{respuesta['total']} citas creadas por los clientes en los siguientes dias"

    # Create message
    subject = f"Citas Informe del {today}"
    elaboracion_fecha_hora_str = datetime.now().strftime("%d/%B/%Y %I:%M%p")
    contenidos = []
    contenidos.append("<style> td {border:2px black solid !important} </style>")
    contenidos.append("<h1>PJECZ Citas V2</h1>")
    contenidos.append(f"<h2>{ccaos_title}</h2>")
    contenidos.append(ccaos_table_html)
    contenidos.append(f"<h2>{cccd_title}</h2>")
    contenidos.append(cccd_table_html)
    contenidos.append(f"<p>Fecha de elaboración: <b>{elaboracion_fecha_hora_str}.</b></p>")
    contenidos.append("<p>ESTE MENSAJE ES ELABORADO POR UN PROGRAMA. FAVOR DE NO RESPONDER.</p>")
    # Send message
    sendgrid_client = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)
    from_email = Email(SENDGRID_FROM_EMAIL)
    to_email = To(email)
    content = Content("text/html", "<br>".join(contenidos))
    mail = Mail(
        from_email=from_email,
        to_emails=to_email,
        subject=subject,
        html_content=content,
    )
    sendgrid_client.client.mail.send.post(request_body=mail.get())

    # Print message to console
    rich.print(f"Mensaje enviado a [blue]{email}[/blue] con [green]{subject}[/green]")


@app.command()
def enviar_agenda_a_usuarios(
    limit: int = 200,
    test: bool = True,
):
    """Enviar la agenda de las citas a los usuarios"""
    rich.print("Enviar la agenda de las citas a los usuarios...")

    # Validar variables de entorno de SendGrid
    try:
        if SENDGRID_API_KEY is None or SENDGRID_API_KEY == "":
            raise lib.exceptions.CLIConfigurationError("Falta SENDGRID_API_KEY")
        if SENDGRID_FROM_EMAIL is None or SENDGRID_FROM_EMAIL == "":
            raise lib.exceptions.CLIConfigurationError("Falta SENDGRID_FROM_EMAIL")
    except lib.exceptions.CLIAnyError as error:
        typer.secho(str(error), fg=typer.colors.RED)
        raise typer.Exit()

    # Inicializar SendGrid
    sendgrid_client = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)
    from_email = Email(SENDGRID_FROM_EMAIL)
    elaboracion_fecha_hora_str = datetime.now().strftime("%d/%B/%Y %I:%M%p")

    # Autenticar
    try:
        base_url = lib.connections.base_url()
        authorization_header = lib.connections.authorization()
    except lib.exceptions.CLIAnyError as error:
        typer.secho(str(error), fg=typer.colors.RED)
        raise typer.Exit()

    # Obtener el proximo dia habil
    try:
        respuesta_cit_dia_disponible = get_cit_dia_disponible(
            base_url=base_url,
            authorization_header=authorization_header,
        )
    except lib.exceptions.CLIAnyError as error:
        typer.secho(str(error), fg=typer.colors.RED)
        raise typer.Exit()
    fecha = respuesta_cit_dia_disponible["fecha"]

    # Obtener las oficinas que pueden agendar citas
    try:
        respuesta_oficinas = get_oficinas(
            base_url=base_url,
            authorization_header=authorization_header,
            limit=limit,
            puede_agendar_citas=True,
        )
    except lib.exceptions.CLIAnyError as error:
        typer.secho(str(error), fg=typer.colors.RED)
        raise typer.Exit()
    oficinas = respuesta_oficinas["items"]

    # Preparar una tabla para mostrar al final
    console = rich.console.Console()
    table = rich.table.Table("Fecha", "Oficina", "Citas", "Destinatarios")

    # Bucle por las oficinas
    for oficina in oficinas:

        # Obtener los usuarios de la oficina
        try:
            respuesta_usuarios = get_usuarios(
                base_url=base_url,
                authorization_header=authorization_header,
                limit=limit,
                oficina_clave=oficina["clave"],
            )
        except lib.exceptions.CLIAnyError as error:
            typer.secho(str(error), fg=typer.colors.RED)
            raise typer.Exit()
        if respuesta_usuarios["total"] == 0:
            rich.print(f"[red]NO HAY DESTINATARIOS[/red] para la oficina [green]{oficina['clave']}[/green]")
            continue
        destinatarios_str = ", ".join([usuario["email"] for usuario in respuesta_usuarios["items"]])

        # Obtener la agenda de las citas de la oficina
        try:
            respuesta_citas = get_cit_citas(
                base_url=base_url,
                authorization_header=authorization_header,
                limit=limit,
                fecha=fecha,
                oficina_clave=oficina["clave"],
            )
        except lib.exceptions.CLIAnyError as error:
            typer.secho(str(error), fg=typer.colors.RED)
            raise typer.Exit()
        if respuesta_citas["total"] == 0:
            citas_str = "SIN CITAS"
        else:
            citas_str = str(respuesta_citas["total"])

        # Agregar un renglon a la tabla
        table.add_row(
            fecha,
            oficina["clave"],
            citas_str,
            destinatarios_str,
        )

        # Comenzar a elaborar el mensaje
        subject = f"Citas de la oficina {oficina['descripcion_corta']} para la fecha {fecha}"
        contenidos = []
        contenidos.append("<style> td {border:2px black solid !important} </style>")
        contenidos.append("<h1>PJECZ Citas V2</h1>")
        contenidos.append(f"<h2>{subject}</h2>")

        # Si no hay citas,
        if respuesta_citas["total"] == 0:
            # El contenido del mensaje es SIN CITAS
            contenidos.append("<p>SIN CITAS AGENDADAS</p>")
        else:
            # El contenido del mensaje es la tabla de citas
            headers = ["Hora", "Nombre", "Servicio", "Notas"]
            rows = []
            for item in respuesta_citas["items"]:
                inicio = datetime.strptime(item["inicio"], "%Y-%m-%dT%H:%M:%S")
                rows.append(
                    [
                        inicio.strftime("%H:%M"),
                        item["cit_cliente_nombre"],
                        item["cit_servicio_clave"],
                        item["notas"],
                    ]
                )
            table_html = tabulate(rows, headers=headers, tablefmt="html")
            table_html = table_html.replace("<table>", '<table border="1" style="width:100%; border: 1px solid black; border-collapse: collapse;">')
            table_html = table_html.replace('<td style="', '<td style="padding: 4px;')
            table_html = table_html.replace("<td>", '<td style="padding: 4px;">')
            contenidos.append(table_html)

        # Parte final del mensaje
        contenidos.append(f"<p>Fecha de elaboración: <b>{elaboracion_fecha_hora_str}.</b></p>")
        contenidos.append("<p>ESTE MENSAJE ES ELABORADO POR UN PROGRAMA. FAVOR DE NO RESPONDER.</p>")
        content = Content("text/html", "<br>".join(contenidos))

        # Mostrar una linea en la terminal
        rich.print(f"Enviando mensaje [blue]{fecha}[/blue] [green]{oficina['clave']}[/green] con [yellow]{citas_str}[/yellow] citas a [cian]{destinatarios_str}[/cian]")

        # Enviar el mensaje
        if test is False:
            to_emails = [destinatario["email"] for destinatario in respuesta_usuarios["items"]]
            mail = Mail(
                from_email=from_email,
                to_emails=to_emails,
                subject=subject,
                html_content=content,
            )
            sendgrid_client.client.mail.send.post(request_body=mail.get())

    # Mostrar la tabla
    console.print(table)
