"""
CLI Base de Datos
"""

import os
import sys
import re
import csv
from datetime import datetime
from pathlib import Path

import click
from dotenv import load_dotenv

from cli.commands.alimentar_autoridades import alimentar_autoridades
from cli.commands.alimentar_distritos import alimentar_distritos, eliminar_distritos_sin_autoridades
from cli.commands.alimentar_domicilios import alimentar_domicilios
from cli.commands.alimentar_materias import alimentar_materias
from cli.commands.alimentar_modulos import alimentar_modulos
from cli.commands.alimentar_oficinas import alimentar_oficinas
from cli.commands.alimentar_permisos import alimentar_permisos
from cli.commands.alimentar_roles import alimentar_roles
from cli.commands.alimentar_usuarios import alimentar_usuarios
from cli.commands.alimentar_usuarios_roles import alimentar_usuarios_roles
from cli.commands.copiar import copiar_tabla
from cli.commands.respaldar_autoridades import respaldar_autoridades
from cli.commands.respaldar_distritos import respaldar_distritos
from cli.commands.respaldar_domicilios import respaldar_domicilios
from cli.commands.respaldar_materias import respaldar_materias
from cli.commands.respaldar_modulos import respaldar_modulos
from cli.commands.respaldar_oficinas import respaldar_oficinas
from cli.commands.respaldar_roles_permisos import respaldar_roles_permisos
from cli.commands.respaldar_usuarios_roles import respaldar_usuarios_roles
from citas_admin.app import create_app
from citas_admin.extensions import database

app = create_app()
app.app_context().push()
database.app = app

load_dotenv()  # Take environment variables from .env

entorno_implementacion = os.environ.get("DEPLOYMENT_ENVIRONMENT", "develop").upper()
RESPALDOS_BASE_DIR = os.getenv("RESPALDOS_BASE_DIR", "")


@click.group()
def cli():
    """Base de Datos"""


@click.command()
def inicializar():
    """Inicializar"""
    if entorno_implementacion == "PRODUCTION":
        click.echo("PROHIBIDO: No se inicializa porque este es el servidor de producción.")
        sys.exit(1)
    database.drop_all()
    database.create_all()
    click.echo("Termina inicializar.")


@click.command()
def alimentar():
    """Alimentar"""
    if entorno_implementacion == "PRODUCTION":
        click.echo("PROHIBIDO: No se alimenta porque este es el servidor de producción.")
        sys.exit(1)
    alimentar_materias()
    alimentar_modulos()
    alimentar_roles()
    alimentar_permisos()
    alimentar_distritos()
    alimentar_autoridades()
    eliminar_distritos_sin_autoridades()
    alimentar_domicilios()
    alimentar_oficinas()
    alimentar_usuarios()
    alimentar_usuarios_roles()
    click.echo("Termina alimentar.")


@click.command()
@click.pass_context
def reiniciar(ctx):
    """Reiniciar ejecuta inicializar y alimentar"""
    ctx.invoke(inicializar)
    ctx.invoke(alimentar)


@click.command()
def respaldar():
    """Respaldar"""
    respaldar_autoridades()
    respaldar_distritos()
    respaldar_domicilios()
    respaldar_materias()
    respaldar_modulos()
    respaldar_oficinas()
    respaldar_roles_permisos()
    respaldar_usuarios_roles()
    click.echo("Termina respaldar.")


@click.command()
def copiar():
    """Copiar los registros de varias tablas desde la BD de origen a la BD de destino"""
    copiar_tabla("cit_categorias")
    copiar_tabla("cit_servicios")
    copiar_tabla("cit_oficinas_servicios")
    copiar_tabla("cit_clientes")
    copiar_tabla("cit_clientes_recuperaciones")
    copiar_tabla("cit_clientes_registros")
    copiar_tabla("cit_dias_inhabiles")
    copiar_tabla("cit_horas_bloqueadas")
    copiar_tabla("cit_citas")
    copiar_tabla("pag_tramites_servicios")
    copiar_tabla("pag_pagos")
    click.echo("Termina copiar.")


@click.command()
@click.argument("anio_mes", type=str)
def generar_csv(anio_mes):
    """Generar CSV para SICGD Respaldos BD"""

    # Validar que la variable de entorno este definida
    if RESPALDOS_BASE_DIR is None or RESPALDOS_BASE_DIR == "":
        click.echo("ERROR: Falta la variable de entorno RESPALDOS_BASE_DIR")
        return

    # Validar que exista y que sea un directorio
    respaldos_base_dir = Path(RESPALDOS_BASE_DIR)
    if not respaldos_base_dir.exists() or not respaldos_base_dir.is_dir():
        click.echo(f"ERROR: No existe o no es directorio {respaldos_base_dir}")
        return

    # Validar que el parámetro mes_int sea YYYY-MM
    if not re.match(r"^\d{4}-\d{2}$", anio_mes):
        click.echo(f"ERROR: {anio_mes} no es una fecha valida (YYYY-MM)")
        return

    # Definir el nombre del archivo CSV que se va a escribir
    output = f"reporte_respaldos_bd_{anio_mes}.csv"

    # Validar que el archivo CSV no exista
    ruta = Path(output)
    if ruta.exists():
        click.echo(f"AVISO: {output} existe, no voy a sobreescribirlo.")
        return

    # Buscar archivos dentro del directorio de respaldo que tengan el nombre buscado
    click.echo("Elaborando reporte de respaldos BD...")
    archivos = []
    nombre_buscado = f"pjecz_citas_v2-{anio_mes[0:4]}-{anio_mes[5:7]}-"
    for archivo in respaldos_base_dir.rglob("*"):
        if nombre_buscado in archivo.name:
            stat = os.stat(archivo)
            patron_fecha = re.search(r"\d{4}-\d{2}-\d{2}-\d{4}", archivo.name)
            patron_fecha = patron_fecha.group()
            fecha = datetime.strptime(patron_fecha, "%Y-%m-%d-%H%M")
            archivo = {
                "fecha": fecha,
                "nombre": archivo.name,
                "tamanio": stat.st_size / (1024 * 1024),
            }
            archivos.append(archivo)

    # Si no se encontraron archivos, salir
    if len(archivos) <= 0:
        click.echo("No se genero el archivo porque no se encontraron archivos.")
        return

    # Escribir el archivo CSV
    with open(ruta, "w", encoding="utf8") as puntero:
        reporte = csv.writer(puntero)
        reporte.writerow(
            [
                "Fecha",
                "Nombre del archivo",
                "Tamaño",
            ]
        )
        for archivo in archivos:
            reporte.writerow(
                [
                    archivo["fecha"].strftime("%Y-%m-%d %H:%M:%S"),
                    archivo["nombre"],
                    f"{archivo['tamanio']:.2f}",
                ]
            )

    # Mostrar en pantalla resultado
    click.echo(f"  |      Fecha       | Nombre                                      | Tamanio (MB)")
    for archivo in archivos:
        click.echo(f"  + {archivo['fecha'].strftime('%Y-%m-%d %H:%M')} | {archivo['nombre']} | {archivo['tamanio']:.2f}")

    # Mostrar mensaje final
    click.echo(f"  {len(archivos)} archivos de respaldo en {ruta.name}")


cli.add_command(inicializar)
cli.add_command(alimentar)
cli.add_command(reiniciar)
cli.add_command(respaldar)
cli.add_command(copiar)
cli.add_command(generar_csv)
