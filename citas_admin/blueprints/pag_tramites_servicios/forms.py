"""
Pag Tramites Servicios, formularios
"""

from flask_wtf import FlaskForm
from wtforms import FloatField, StringField, SubmitField
from wtforms.validators import DataRequired, Length, Regexp

from lib.safe_string import CLAVE_REGEXP


class PagTramiteServicioForm(FlaskForm):
    """Formulario PagTramiteServicio"""

    clave = StringField("Clave (única de hasta 16 caracteres)", validators=[DataRequired(), Regexp(CLAVE_REGEXP)])
    descripcion = StringField("Descripción", validators=[DataRequired(), Length(max=256)])
    costo = FloatField("Costo", validators=[DataRequired()])
    url = StringField("URL", validators=[DataRequired(), Length(max=256)])
    guardar = SubmitField("Guardar")
