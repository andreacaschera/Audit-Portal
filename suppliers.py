from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from sqlalchemy import func
from models import db, Fornitore, FornitoreQualifica
from forms import SupplierQualifyForm

suppliers_bp = Blueprint("suppliers", __name__)

@suppliers_bp.route("/")
@login_required
def index():
    return render_template("qualifica_fornitori.html")

@suppliers_bp.route("/elenco")
@login_required
def elenco():
    # Elenco dei fornitori con almeno una qualifica (si mostra l'ultima)
    items = []
    fornitori = Fornitore.query.order_by(Fornitore.nome.asc()).all()
    for f in fornitori:
        last_q = f.qualifiche.order_by(FornitoreQualifica.created_at.desc()).first()
        if last_q:
            items.append({"fornitore": f, "qualifica": last_q, "score": last_q.final_score})
    return render_template("fornitori_elenco.html", items=items)

@suppliers_bp.route("/nuovo", methods=["GET", "POST"])
@login_required
def nuovo():
    form = SupplierQualifyForm()
    if form.validate_on_submit():
        # Crea fornitore
        f = Fornitore(
            nome=(form.nome.data or '').strip(),
            indirizzo=(form.indirizzo.data or '').strip(),
            citta=(form.citta.data or '').strip(),
            tipologia=(form.tipologia.data or '').strip(),
            contatto=(form.contatto.data or '').strip(),
            email=(form.email.data or '').strip(),
        )
        db.session.add(f)
        db.session.flush()
        # Prima qualifica
        q = FornitoreQualifica(
            fornitore_id=f.id,
            q1_req=form.q1_req.data, q1_imp=form.q1_imp.data,
            q2_req=form.q2_req.data, q2_imp=form.q2_imp.data,
            q3_req=form.q3_req.data, q3_imp=form.q3_imp.data,
            q4_req=form.q4_req.data, q4_imp=form.q4_imp.data,
            q5_req=form.q5_req.data, q5_imp=form.q5_imp.data,
            q6_req=form.q6_req.data, q6_imp=form.q6_imp.data,
            q7_req=form.q7_req.data, q7_imp=form.q7_imp.data,
            q8_req=form.q8_req.data, q8_imp=form.q8_imp.data,
            q9_req=form.q9_req.data, q9_imp=form.q9_imp.data,
            q10_req=form.q10_req.data, q10_imp=form.q10_imp.data,
            note=(form.note.data or '').strip(),
        )
        db.session.add(q)
        db.session.commit()
        flash("Fornitore creato e qualificato.", "success")
        return redirect(url_for("suppliers.elenco"))
    return render_template("fornitore_qualifica_form.html", form=form, mode="nuovo")

@suppliers_bp.route("/rivaluta")
@login_required
def rivaluta_list():
    # Solo fornitori già qualificati
    fornitori = (
        Fornitore.query
        .join(FornitoreQualifica, Fornitore.id == FornitoreQualifica.fornitore_id)
        .group_by(Fornitore.id)
        .order_by(Fornitore.nome.asc())
        .all()
    )
    return render_template("fornitori_rivaluta_seleziona.html", fornitori=fornitori)

@suppliers_bp.route("/rivaluta/<int:fid>", methods=["GET", "POST"])
@login_required
def rivaluta(fid):
    f = Fornitore.query.get_or_404(fid)
    last_q = f.qualifiche.order_by(FornitoreQualifica.created_at.desc()).first()
    form = SupplierQualifyForm(obj=f)
    # Precompila con l'ultima qualifica
    if request.method == "GET" and last_q:
        for i in range(1, 11):
            getattr(form, f"q{i}_req").data = getattr(last_q, f"q{i}_req")
            getattr(form, f"q{i}_imp").data = getattr(last_q, f"q{i}_imp")
        form.note.data = last_q.note or ""
    if form.validate_on_submit():
        f.nome = (form.nome.data or '').strip()
        f.indirizzo = (form.indirizzo.data or '').strip()
        f.citta = (form.citta.data or '').strip()
        f.tipologia = (form.tipologia.data or '').strip()
        f.contatto = (form.contatto.data or '').strip()
        f.email = (form.email.data or '').strip()
        q = FornitoreQualifica(
            fornitore_id=f.id,
            q1_req=form.q1_req.data, q1_imp=form.q1_imp.data,
            q2_req=form.q2_req.data, q2_imp=form.q2_imp.data,
            q3_req=form.q3_req.data, q3_imp=form.q3_imp.data,
            q4_req=form.q4_req.data, q4_imp=form.q4_imp.data,
            q5_req=form.q5_req.data, q5_imp=form.q5_imp.data,
            q6_req=form.q6_req.data, q6_imp=form.q6_imp.data,
            q7_req=form.q7_req.data, q7_imp=form.q7_imp.data,
            q8_req=form.q8_req.data, q8_imp=form.q8_imp.data,
            q9_req=form.q9_req.data, q9_imp=form.q9_imp.data,
            q10_req=form.q10_req.data, q10_imp=form.q10_imp.data,
            note=(form.note.data or '').strip(),
        )
        db.session.add(q)
        db.session.commit()
        flash("Qualifica aggiornata.", "success")
        return redirect(url_for("suppliers.elenco"))
    return render_template("fornitore_qualifica_form.html", form=form, mode="rivaluta", fornitore=f)

@suppliers_bp.route("/elimina/<int:fid>", methods=["POST"])
@login_required
def elimina(fid):
    f = Fornitore.query.get_or_404(fid)
    # elimina prima le qualifiche per vincoli FK
    for q in f.qualifiche.all():
        db.session.delete(q)
    db.session.delete(f)
    db.session.commit()
    flash("Fornitore eliminato.", "success")
    return redirect(url_for("suppliers.elenco"))

