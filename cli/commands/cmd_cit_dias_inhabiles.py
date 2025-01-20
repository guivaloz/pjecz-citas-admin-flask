"""
CLI Días Inhábiles

- eliminar: Eliminar los días inhábiles pasados
"""

from datetime import datetime
import click

from citas_admin.app import create_app
from citas_admin.blueprints.cit_dias_inhabiles.models import CitDiaInhabil
from citas_admin.extensions import database

app = create_app()
app.app_context().push()
database.app = app


@click.group()
def cli():
    """Cit Dias Inhábiles"""


@click.command()
def eliminar():
    """Eliminar los días inhábiles pasados"""
    click.echo("Eliminar los días inhábiles pasados: ", nl=False)
    contador = 0
    cit_dias_inhabiles = CitDiaInhabil.query.filter_by(estatus="A").all()
    for cit_dia_inhabil in cit_dias_inhabiles:
        if cit_dia_inhabil.fecha < datetime.now().date():
            click.echo(click.style("-", fg="red"), nl=False)
            cit_dia_inhabil.delete()
            contador += 1
    click.echo()
    click.echo(click.style(f"Se eliminaron {contador} días inhábiles pasados", fg="green"))


cli.add_command(eliminar)
