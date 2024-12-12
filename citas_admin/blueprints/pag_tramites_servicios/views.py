"""
Pag Tramites Servicios, vistas
"""

import json

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from citas_admin.blueprints.bitacoras.models import Bitacora
from citas_admin.blueprints.modulos.models import Modulo
from citas_admin.blueprints.pag_pagos.models import PagPago
from citas_admin.blueprints.pag_tramites_servicios.models import PagTramiteServicio
from citas_admin.blueprints.pag_tramites_servicios.forms import PagTramiteServicioForm
from citas_admin.blueprints.permisos.models import Permiso
from citas_admin.blueprints.usuarios.decorators import permission_required
from lib.datatables import get_datatable_parameters, output_datatable_json
from lib.safe_string import safe_clave, safe_message, safe_string

MODULO = "PAG TRAMITES SERVICIOS"

pag_tramites_servicios = Blueprint("pag_tramites_servicios", __name__, template_folder="templates")


@pag_tramites_servicios.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@pag_tramites_servicios.route("/pag_tramites_servicios/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de PagTramiteServicio"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = PagTramiteServicio.query
    # Primero filtrar por columnas propias
    if "estatus" in request.form:
        consulta = consulta.filter_by(estatus=request.form["estatus"])
    else:
        consulta = consulta.filter_by(estatus="A")
    if "clave" in request.form:
        clave = safe_clave(request.form["clave"])
        if clave != "":
            consulta = consulta.filter(PagTramiteServicio.clave.contains(clave))
    if "descripcion" in request.form:
        descripcion = safe_string(request.form["descripcion"], save_enie=True)
        if descripcion != "":
            consulta = consulta.filter(PagTramiteServicio.descripcion.contains(descripcion))
    # Ordenar y paginar
    registros = consulta.order_by(PagTramiteServicio.clave).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for resultado in registros:
        data.append(
            {
                "detalle": {
                    "clave": resultado.clave,
                    "url": url_for("pag_tramites_servicios.detail", pag_tramite_servicio_id=resultado.id),
                },
                "descripcion": resultado.descripcion,
                "costo": resultado.costo,
                "url": resultado.url,
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@pag_tramites_servicios.route("/pag_tramites_servicios")
def list_active():
    """Listado de PagTramiteServicio activos"""
    return render_template(
        "pag_tramites_servicios/list.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Trámites y Servicios",
        estatus="A",
    )


@pag_tramites_servicios.route("/pag_tramites_servicios/inactivos")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def list_inactive():
    """Listado de PagTramiteServicio inactivos"""
    return render_template(
        "pag_tramites_servicios/list.jinja2",
        filtros=json.dumps({"estatus": "B"}),
        titulo="Trámites y Servicios inactivos",
        estatus="B",
    )


@pag_tramites_servicios.route("/pag_tramites_servicios/<int:pag_tramite_servicio_id>")
def detail(pag_tramite_servicio_id):
    """Detalle de un PagTramiteServicio"""
    pag_tramite_servicio = PagTramiteServicio.query.get_or_404(pag_tramite_servicio_id)
    return render_template(
        "pag_tramites_servicios/detail.jinja2",
        pag_tramite_servicio=pag_tramite_servicio,
        pag_pagos_estados=PagPago.ESTADOS,
    )


@pag_tramites_servicios.route("/pag_tramites_servicios/tablero")
def dashboard():
    """Tablero de PagTramiteServicio"""
    return render_template(
        "pag_tramites_servicios/dashboard.jinja2",
        pag_tramites_servicios=PagTramiteServicio.query.filter_by(estatus="A").order_by(PagTramiteServicio.clave).all(),
    )


@pag_tramites_servicios.route("/pag_tramites_servicios/nuevo", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.CREAR)
def new():
    """Nuevo PagTramiteServicio"""
    form = PagTramiteServicioForm()
    if form.validate_on_submit():
        es_valido = True
        # Validar que la clave no se repita
        clave = safe_clave(form.clave.data)
        if PagTramiteServicio.query.filter_by(clave=clave).first():
            flash("La clave ya está en uso. Debe de ser única.", "warning")
            es_valido = False
        # Si es válido, guardar
        if es_valido is True:
            pag_tramite_servicio = PagTramiteServicio(
                clave=clave,
                descripcion=safe_string(form.descripcion.data, save_enie=True),
                costo=form.costo.data,
                url=form.url.data,
            )
            pag_tramite_servicio.save()
            bitacora = Bitacora(
                modulo=Modulo.query.filter_by(nombre=MODULO).first(),
                usuario=current_user,
                descripcion=safe_message(f"Nuevo Trámite y Servicio {pag_tramite_servicio.clave}"),
                url=url_for("pag_tramites_servicios.detail", pag_tramite_servicio_id=pag_tramite_servicio.id),
            )
            bitacora.save()
            flash(bitacora.descripcion, "success")
            return redirect(bitacora.url)
    return render_template("pag_tramites_servicios/new.jinja2", form=form)


@pag_tramites_servicios.route("/pag_tramites_servicios/edicion/<int:pag_tramite_servicio_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.MODIFICAR)
def edit(pag_tramite_servicio_id):
    """Editar PagTramiteServicio"""
    pag_tramite_servicio = PagTramiteServicio.query.get_or_404(pag_tramite_servicio_id)
    form = PagTramiteServicioForm()
    if form.validate_on_submit():
        es_valido = True
        # Si cambia la clave verificar que no este en uso
        clave = safe_clave(form.clave.data)
        if pag_tramite_servicio.clave != clave:
            pag_tramite_servicio_existente = PagTramiteServicio.query.filter_by(clave=clave).first()
            if pag_tramite_servicio_existente and pag_tramite_servicio_existente.id != pag_tramite_servicio.id:
                es_valido = False
                flash("La clave ya está en uso. Debe de ser única.", "warning")
        # Si es válido, actualizar
        if es_valido:
            pag_tramite_servicio.clave = clave
            pag_tramite_servicio.descripcion = safe_string(form.descripcion.data, save_enie=True)
            pag_tramite_servicio.costo = form.costo.data
            pag_tramite_servicio.url = form.url.data
            pag_tramite_servicio.save()
            bitacora = Bitacora(
                modulo=Modulo.query.filter_by(nombre=MODULO).first(),
                usuario=current_user,
                descripcion=safe_message(f"Editado Trámite y Servicio {pag_tramite_servicio.clave}"),
                url=url_for("pag_tramites_servicios.detail", pag_tramite_servicio_id=pag_tramite_servicio.id),
            )
            bitacora.save()
            flash(bitacora.descripcion, "success")
            return redirect(bitacora.url)
    form.clave.data = pag_tramite_servicio.clave
    form.descripcion.data = pag_tramite_servicio.descripcion
    form.costo.data = pag_tramite_servicio.costo
    form.url.data = pag_tramite_servicio.url
    return render_template(
        "pag_tramites_servicios/edit.jinja2",
        form=form,
        pag_tramite_servicio=pag_tramite_servicio,
    )


@pag_tramites_servicios.route("/pag_tramites_servicios/eliminar/<int:pag_tramite_servicio_id>")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def delete(pag_tramite_servicio_id):
    """Eliminar PagTramiteServicio"""
    pag_tramite_servicio = PagTramiteServicio.query.get_or_404(pag_tramite_servicio_id)
    if pag_tramite_servicio.estatus == "A":
        pag_tramite_servicio.delete()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Eliminado Trámite y Servicio {pag_tramite_servicio.clave}"),
            url=url_for("pag_tramites_servicios.detail", pag_tramite_servicio_id=pag_tramite_servicio.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("pag_tramites_servicios.detail", pag_tramite_servicio_id=pag_tramite_servicio.id))


@pag_tramites_servicios.route("/pag_tramites_servicios/recuperar/<int:pag_tramite_servicio_id>")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def recover(pag_tramite_servicio_id):
    """Recuperar PagTramiteServicio"""
    pag_tramite_servicio = PagTramiteServicio.query.get_or_404(pag_tramite_servicio_id)
    if pag_tramite_servicio.estatus == "B":
        pag_tramite_servicio.recover()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Recuperado Trámite y Servicio {pag_tramite_servicio.clave}"),
            url=url_for("pag_tramites_servicios.detail", pag_tramite_servicio_id=pag_tramite_servicio.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("pag_tramites_servicios.detail", pag_tramite_servicio_id=pag_tramite_servicio.id))
