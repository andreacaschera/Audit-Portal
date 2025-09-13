import os
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_from_directory, current_app
from flask_login import login_required
from werkzeug.utils import secure_filename
from models import db
from training_models import Course, Candidate, Enrollment
from training_forms import NewCourseForm, CandidateForm

training_bp = Blueprint("training", __name__)

PASS_THRESHOLD = 60  # %

DEFAULT_EXAM_QUESTIONS = [
    {"q": "Il docente definisce gli obiettivi del corso all'inizio?", "opts": ["Sì", "No"], "answer": 0},
    {"q": "È obbligatorio completare il materiale prima dell'esame?", "opts": ["Sì", "No"], "answer": 0},
    {"q": "La validità di un corso può essere espressa in mesi?", "opts": ["Sì", "No"], "answer": 0},
    {"q": "I materiali video non possono essere caricati.", "opts": ["Vero", "Falso"], "answer": 1},
    {"q": "L'attestato si genera solo se il test è superato.", "opts": ["Sì", "No"], "answer": 0},
]

def _ensure_dirs():
    inst = current_app.instance_path
    mats = os.path.join(inst, "training_materials")
    certs = os.path.join(inst, "certificates")
    os.makedirs(mats, exist_ok=True)
    os.makedirs(certs, exist_ok=True)
    return mats, certs

@training_bp.route("/")
@login_required
def index():
    return render_template("formazione/index.html")

@training_bp.route("/nuovo-corso", methods=["GET", "POST"])
@login_required
def new_course():
    mats_dir, _ = _ensure_dirs()
    form = NewCourseForm()
    if form.validate_on_submit():
        c = Course(
            title=form.title.data.strip(),
            teacher=form.teacher.data.strip(),
            validity_months=form.validity_months.data,
        )
        file = form.material.data
        if file:
            filename = secure_filename(file.filename)
            if filename:
                path = os.path.join(mats_dir, filename)
                file.save(path)
                c.material_filename = filename
                c.material_mimetype = file.mimetype or ""
        db.session.add(c)
        db.session.commit()
        flash("Corso creato con successo.", "success")
        return redirect(url_for("training.index"))
    return render_template("formazione/new_course.html", form=form)

@training_bp.route("/registra-candidato", methods=["GET", "POST"])
@login_required
def register_candidate():
    form = CandidateForm()
    if form.validate_on_submit():
        cand = Candidate(
            first_name=form.first_name.data.strip(),
            last_name=form.last_name.data.strip(),
            place_of_birth=(form.place_of_birth.data or "").strip(),
            date_of_birth=form.date_of_birth.data,
            role=(form.role.data or "").strip(),
        )
        db.session.add(cand)
        db.session.commit()
        return redirect(url_for("training.select_course", candidate_id=cand.id))
    return render_template("formazione/register_candidate.html", form=form)

@training_bp.route("/seleziona-corso")
@login_required
def select_course():
    candidate_id = request.args.get("candidate_id", type=int)
    if not candidate_id:
        return redirect(url_for("training.register_candidate"))
    courses = Course.query.order_by(Course.created_at.desc()).all()
    return render_template("formazione/select_course.html", courses=courses, candidate_id=candidate_id)

@training_bp.route("/iscrivi", methods=["POST"])
@login_required
def enroll():
    candidate_id = request.form.get("candidate_id", type=int)
    course_id = request.form.get("course_id", type=int)
    if not (candidate_id and course_id):
        flash("Selezione non valida.", "warning")
        return redirect(url_for("training.index"))
    enr = Enrollment.query.filter_by(candidate_id=candidate_id, course_id=course_id).first()
    if not enr:
        enr = Enrollment(candidate_id=candidate_id, course_id=course_id)
        db.session.add(enr)
        db.session.commit()
    return redirect(url_for("training.view_material", enrollment_id=enr.id))

@training_bp.route("/materiale/<int:enrollment_id>")
@login_required
def view_material(enrollment_id):
    enr = Enrollment.query.get_or_404(enrollment_id)
    course = enr.course
    mats_dir, _ = _ensure_dirs()
    file_url = None
    is_video = False
    if course.material_filename:
        file_url = url_for("training.materials", filename=course.material_filename)
        mt = (course.material_mimetype or "").lower()
        is_video = any(x in mt for x in ["video", "mp4", "webm", "ogg"])
    return render_template("formazione/view_material.html", enrollment=enr, course=course, file_url=file_url, is_video=is_video)

@training_bp.route("/materiali/<path:filename>")
@login_required
def materials(filename):
    mats_dir, _ = _ensure_dirs()
    return send_from_directory(mats_dir, filename, as_attachment=False)

@training_bp.route("/esame/<int:enrollment_id>", methods=["GET", "POST"])
@login_required
def exam(enrollment_id):
    from flask_wtf import FlaskForm
    from wtforms import RadioField, SubmitField
    enr = Enrollment.query.get_or_404(enrollment_id)
    class DynamicExamForm(FlaskForm):
        submit = SubmitField("Invia test")
    # build fields dynamically
    for idx, q in enumerate(DEFAULT_EXAM_QUESTIONS):
        setattr(DynamicExamForm, f"q{idx}", RadioField(q["q"], choices=[(str(i), opt) for i, opt in enumerate(q["opts"])]))
    form = DynamicExamForm()
    if form.validate_on_submit():
        correct = 0
        for idx, q in enumerate(DEFAULT_EXAM_QUESTIONS):
            val = getattr(form, f"q{idx}").data
            if val is not None and int(val) == int(q["answer"]):
                correct += 1
        total = len(DEFAULT_EXAM_QUESTIONS)
        score = int(round(correct * 100.0 / total))
        enr.exam_score = score
        enr.exam_passed = score >= PASS_THRESHOLD
        db.session.commit()
        if enr.exam_passed:
            _, certs_dir = _ensure_dirs()
            cert_name = f"attestato_enrollment_{enrollment_id}.pdf"
            cert_path = os.path.join(certs_dir, cert_name)
            _generate_certificate_pdf(cert_path, enr)
            enr.certificate_path = cert_name
            db.session.commit()
            return render_template("formazione/certificate_ready.html", enrollment=enr, course=enr.course, cert_url=url_for("training.certificate", filename=cert_name))
        else:
            flash(f"Test non superato ({score}%).", "warning")
            return redirect(url_for("training.exam", enrollment_id=enrollment_id))
    return render_template("formazione/exam.html", form=form, enrollment=enr, course=enr.course, questions=DEFAULT_EXAM_QUESTIONS)

@training_bp.route("/attestati/<path:filename>")
@login_required
def certificate(filename):
    _, certs_dir = _ensure_dirs()
    return send_from_directory(certs_dir, filename, as_attachment=True)



@training_bp.get("/corsisti")
@login_required
def corsisti_list():
    """Elenco corsisti iscritti ai corsi, con stato esame e azioni."""
    enrollments = Enrollment.query.order_by(Enrollment.id.desc()).all()
    return render_template("formazione/elenco_corsisti.html", enrollments=enrollments)

@training_bp.post("/enrollments/<int:enrollment_id>/delete")
@login_required
def delete_enrollment(enrollment_id: int):
    """Elimina l'iscrizione (corsista) dal corso."""
    enr = Enrollment.query.get_or_404(enrollment_id)
    db.session.delete(enr)
    db.session.commit()
    flash("Corsista eliminato dal corso.", "success")
    return redirect(url_for("training.corsisti_list"))

def _generate_certificate_pdf(path, enrollment):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import cm
        from reportlab.pdfgen import canvas
        c = canvas.Canvas(path, pagesize=A4)
        width, height = A4
        c.setFont("Helvetica-Bold", 20)
        c.drawCentredString(width/2, height-3*cm, "ATTESTATO DI FREQUENZA")
        c.setFont("Helvetica", 12)
        candidate = f"{enrollment.candidate.first_name} {enrollment.candidate.last_name}".strip()
        course = enrollment.course.title
        date_str = datetime.utcnow().strftime("%d/%m/%Y")
        lines = [
            f"Si certifica che {candidate} ha superato il test di valutazione",
            f"relativo al corso: \"{course}\"",
            f"Data: {date_str}  -  Punteggio: {enrollment.exam_score}%"
        ]
        y = height - 5*cm
        for line in lines:
            c.drawCentredString(width/2, y, line); y -= 1*cm
        c.setFont("Helvetica-Oblique", 10)
        c.drawRightString(width-2*cm, 2*cm, "Generato automaticamente dal sistema")
        c.showPage(); c.save()
    except Exception:
        with open(path, "wb") as f:
            f.write(b"%PDF-1.4\n% Fallback attestato\n")
