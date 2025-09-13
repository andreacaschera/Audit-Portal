
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
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
    # Supplier is considered "qualificato" if has at least one qualifica; take the latest
    data = []
    fornitori = Fornitore.query.order_by(Fornitore.nome.asc()).all()
    for f in fornitori:
        last_q = f.qualifiche.order_by(FornitoreQualifica.created_at.desc()).first()
        if last_q:
            data.append({
                "fornitore": f,
                "qualifica": last_q,
                "score": last_q.final_score
            })
    return render_template("fornitori_elenco.html", items=data)

@suppliers_bp.route("/nuovo", methods=["GET", "POST"])
@login_required
def nuovo():
    form = SupplierQualifyForm()
    if form.validate_on_submit():
        # Create supplier
        f = Fornitore(
            nome=form.nome.data.strip(),
            indirizzo=(form.indirizzo.data or "").strip(),
            citta=(form.citta.data or "").strip(),
            tipologia=form.tipologia.data.strip(),
            contatto=(form.contatto.data or "").strip(),
        )
        db.session.add(f)
        db.session.flush()
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
            note=form.note.data
        )
        db.session.add(q)
        db.session.commit()
        flash("Fornitore creato e qualificato.", "success")
        return redirect(url_for("suppliers.elenco"))
    return render_template("fornitore_qualifica_form.html", form=form, mode="nuovo")

@suppliers_bp.route("/rivaluta")
@login_required
def rivaluta_list():
    # List qualified suppliers (with at least one qualifica)
    fornitori = (
        Fornitore.query
        .join(FornitoreQualifica, Fornitore.id == FornitoreQualifica.fornitore_id)
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
    # Pre-fill from last qualification
    if request.method == "GET" and last_q:
        for i in range(1, 11):
            setattr(form, f"q{i}_req", getattr(form, f"q{i}_req"))
            getattr(form, f"q{i}_req").data = getattr(last_q, f"q{i}_req")
            getattr(form, f"q{i}_imp").data = getattr(last_q, f"q{i}_imp")
        form.note.data = last_q.note or ""
    if form.validate_on_submit():
        # update supplier base fields if changed
        f.nome = form.nome.data.strip()
        f.indirizzo = (form.indirizzo.data or "").strip()
        f.citta = (form.citta.data or "").strip()
        f.tipologia = form.tipologia.data.strip()
        f.contatto = (form.contatto.data or "").strip()
        # new qualification entry
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
            note=form.note.data
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
    # delete qualifications first due to FK
    for q in f.qualifiche.all():
        db.session.delete(q)
    db.session.delete(f)
    db.session.commit()
    flash("Fornitore eliminato.", "success")
    return redirect(url_for("suppliers.elenco"))
