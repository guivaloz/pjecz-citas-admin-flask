"""
Alimentar Autoridades
"""

import csv
import sys
from pathlib import Path

import click

from citas_admin.blueprints.autoridades.models import Autoridad
from citas_admin.blueprints.distritos.models import Distrito
from citas_admin.blueprints.materias.models import Materia
from lib.safe_string import safe_clave, safe_string

AUTORIDADES_CSV = "seed/autoridades.csv"


def alimentar_autoridades():
    """Alimentar Autoridades"""
    ruta = Path(AUTORIDADES_CSV)
    if not ruta.exists():
        click.echo(f"AVISO: {ruta.name} no se encontró.")
        sys.exit(1)
    if not ruta.is_file():
        click.echo(f"AVISO: {ruta.name} no es un archivo.")
        sys.exit(1)
    click.echo("Alimentando autoridades: ", nl=False)
    contador = 0
    with open(ruta, encoding="utf8") as puntero:
        rows = csv.DictReader(puntero)
        for row in rows:
            autoridad_id = int(row["autoridad_id"])
            distrito_id = int(row["distrito_id"])
            materia_id = int(row["materia_id"])
            clave = safe_clave(row["clave"])
            descripcion = safe_string(row["descripcion"], save_enie=True)
            descripcion_corta = safe_string(row["descripcion_corta"], save_enie=True)
            es_jurisdiccional = row["es_jurisdiccional"] == "1"
            es_notaria = row["es_notaria"] == "1"
            organo_jurisdiccional = safe_string(row["organo_jurisdiccional"], save_enie=True)
            estatus = row["estatus"]
            if autoridad_id != contador + 1:
                click.echo(click.style(f"  AVISO: autoridad_id {autoridad_id} no es consecutivo", fg="red"))
                sys.exit(1)
            distrito = Distrito.query.get(distrito_id)
            if distrito is None:
                click.echo(click.style(f"  AVISO: distrito_id {distrito_id} no existe", fg="red"))
                sys.exit(1)
            materia = Materia.query.get(materia_id)
            if materia is None:
                click.echo(click.style(f"  AVISO: materia_id {materia_id} no existe", fg="red"))
                sys.exit(1)
            Autoridad(
                distrito=distrito,
                materia=materia,
                clave=clave,
                descripcion=descripcion,
                descripcion_corta=descripcion_corta,
                es_jurisdiccional=es_jurisdiccional,
                es_notaria=es_notaria,
                organo_jurisdiccional=organo_jurisdiccional,
                estatus=estatus,
            ).save()
            contador += 1
            click.echo(click.style(".", fg="green"), nl=False)
    click.echo()
    click.echo(click.style(f"  {contador} autoridades alimentadas.", fg="green"))
