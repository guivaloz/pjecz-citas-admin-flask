"""
Respaldar Materias
"""

import csv
import sys
from pathlib import Path

import click

from citas_admin.blueprints.materias.models import Materia

MATERIAS_CSV = "seed/materias.csv"


def respaldar_materias():
    """Respaldar Materias"""
    ruta = Path(MATERIAS_CSV)
    if ruta.exists():
        click.echo(f"AVISO: {MATERIAS_CSV} ya existe, no voy a sobreescribirlo.")
        sys.exit(1)
    click.echo("Respaldando materias: ", nl=False)
    contador = 0
    with open(ruta, "w", encoding="utf8") as puntero:
        respaldo = csv.writer(puntero)
        respaldo.writerow(
            [
                "materia_id",
                "nombre",
                "estatus",
            ]
        )
        for materia in Materia.query.order_by(Materia.id).all():
            respaldo.writerow(
                [
                    materia.id,
                    materia.nombre,
                    materia.estatus,
                ]
            )
            contador += 1
            click.echo(click.style(".", fg="green"), nl=False)
    click.echo()
    click.echo(click.style(f"  {contador} materias respaldadas.", fg="green"))
