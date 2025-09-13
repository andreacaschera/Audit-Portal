from datetime import date
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DateField, IntegerField, DecimalField, SubmitField
from wtforms.validators import DataRequired, Optional

def _std_choices():
    return [
        ("ISO 9001", "ISO 9001"),
        ("ISO 14001", "ISO 14001"),
        ("ISO 45001", "ISO 45001"),
        ("ISO 37001", "ISO 37001"),
        ("UNI/PdR 125", "UNI/PdR 125"),
        ("Altro", "Altro"),
    ]

class NuovoAuditForm(FlaskForm):
    titolo = StringField("Titolo audit", validators=[DataRequired()])
    codice = StringField("Codice audit", validators=[DataRequired()])
    data_audit = DateField("Data audit", validators=[DataRequired()], default=date.today)
    cliente = StringField("Cliente", validators=[Optional()])
    sede = StringField("Sede", validators=[Optional()])
    norma = SelectField("Norma di riferimento", choices=_std_choices(), validators=[Optional()])
    stato = SelectField("Stato", choices=[("Pianificato","Pianificato"),("In corso","In corso"),("Chiuso","Chiuso")])
    submit = SubmitField("Salva audit")

class SelezionaAuditForm(FlaskForm):
    # Popolato dinamicamente nella view
    audit_id = SelectField("Scegli un audit", coerce=int, validators=[DataRequired()])
    submit = SubmitField("Apri")

class NuovaNCForm(FlaskForm):
    codice = StringField("Codice NC", validators=[DataRequired()])
    descrizione = TextAreaField("Descrizione", validators=[DataRequired()])
    gravita = SelectField("Gravità", choices=[("Minore","Minore"),("Maggiore","Maggiore"),("Critica","Critica")])
    categoria = StringField("Categoria", validators=[Optional()])
    rilevata_da = StringField("Rilevata da", validators=[Optional()])
    data_apertura = DateField("Data apertura", default=date.today, validators=[Optional()])
    stato = SelectField("Stato", choices=[("Aperta","Aperta"),("In corso","In corso"),("Chiusa","Chiusa")])
    submit = SubmitField("Salva NC")

class NuovaAzioneForm(FlaskForm):
    azione = TextAreaField("Azione correttiva", validators=[DataRequired()])
    responsabile = StringField("Responsabile", validators=[Optional()])
    data_scadenza = DateField("Data scadenza", validators=[Optional()])
    stato = SelectField("Stato", choices=[("Aperta","Aperta"),("In corso","In corso"),("Chiusa","Chiusa")])
    efficacia = SelectField("Efficacia", choices=[("Da Verificare","Da Verificare"),("Efficace","Efficace"),("Non Efficace","Non Efficace")])
    submit = SubmitField("Salva azione")

# ---- Dynamic field factory ----

from wtforms import Field
from wtforms.widgets import TextArea, Input

def dynamic_fields_to_form(form_cls, custom_fields):
    """
    Aggiunge campi custom a una classe di form WTForms in base alle definizioni.
    """
    for cf in custom_fields:
        field = None
        validators = [DataRequired()] if cf.required else [Optional()]
        if cf.field_type == "text":
            field = StringField(cf.label, validators=validators)
        elif cf.field_type == "textarea":
            field = TextAreaField(cf.label, validators=validators)
        elif cf.field_type == "integer":
            field = IntegerField(cf.label, validators=validators)
        elif cf.field_type == "decimal":
            field = DecimalField(cf.label, validators=validators, places=2)
        elif cf.field_type == "date":
            field = DateField(cf.label, validators=validators)
        elif cf.field_type == "select":
            import json
            opts = []
            try:
                opts = json.loads(cf.options) if cf.options else []
            except Exception:
                opts = []
            field = SelectField(cf.label, choices=[(o,o) for o in opts], validators=validators)
        if field:
            setattr(form_cls, f"cf_{cf.id}", field)
    return form_cls


class SupplierBaseForm(FlaskForm):
    nome = StringField("Ragione sociale", validators=[DataRequired()])
    indirizzo = StringField("Indirizzo", validators=[Optional()])
    citta = StringField("Città", validators=[Optional()])
    tipologia = StringField("Tipologia del servizio/fornitura", validators=[DataRequired()])
    contatto = StringField("Persona di contatto", validators=[Optional()])

def _mk_select(name, label, choices):
    return SelectField(label, choices=choices, validators=[DataRequired()], coerce=int, name=name)

class SupplierQualifyForm(SupplierBaseForm):
    # Requisito (1-5) e Importanza (1-6) per ciascuna domanda
    q1_req = SelectField("1. Presenza di certificazioni — Requisito (1-5)", choices=[(i, str(i)) for i in range(1,6)], coerce=int, validators=[DataRequired()])
    q1_imp = SelectField("Importanza (1-6)", choices=[(i, str(i)) for i in range(1,7)], coerce=int, validators=[DataRequired()])
    q2_req = SelectField("2. Prezzo competitivo — Requisito (1-5)", choices=[(i, str(i)) for i in range(1,6)], coerce=int, validators=[DataRequired()])
    q2_imp = SelectField("Importanza (1-6)", choices=[(i, str(i)) for i in range(1,7)], coerce=int, validators=[DataRequired()])
    q3_req = SelectField("3. Fornitore storico — Requisito (1-5)", choices=[(i, str(i)) for i in range(1,6)], coerce=int, validators=[DataRequired()])
    q3_imp = SelectField("Importanza (1-6)", choices=[(i, str(i)) for i in range(1,7)], coerce=int, validators=[DataRequired()])
    q4_req = SelectField("4. Rispetto dei tempi di consegna — Requisito (1-5)", choices=[(i, str(i)) for i in range(1,6)], coerce=int, validators=[DataRequired()])
    q4_imp = SelectField("Importanza (1-6)", choices=[(i, str(i)) for i in range(1,7)], coerce=int, validators=[DataRequired()])
    q5_req = SelectField("5. Tempestività nelle richieste — Requisito (1-5)", choices=[(i, str(i)) for i in range(1,6)], coerce=int, validators=[DataRequired()])
    q5_imp = SelectField("Importanza (1-6)", choices=[(i, str(i)) for i in range(1,7)], coerce=int, validators=[DataRequired()])
    q6_req = SelectField("6. Modalità di pagamento — Requisito (1-5)", choices=[(i, str(i)) for i in range(1,6)], coerce=int, validators=[DataRequired()])
    q6_imp = SelectField("Importanza (1-6)", choices=[(i, str(i)) for i in range(1,7)], coerce=int, validators=[DataRequired()])
    q7_req = SelectField("7. Esperienza — Requisito (1-5)", choices=[(i, str(i)) for i in range(1,6)], coerce=int, validators=[DataRequired()])
    q7_imp = SelectField("Importanza (1-6)", choices=[(i, str(i)) for i in range(1,7)], coerce=int, validators=[DataRequired()])
    q8_req = SelectField("8. Disponibilità a ricevere audit — Requisito (1-5)", choices=[(i, str(i)) for i in range(1,6)], coerce=int, validators=[DataRequired()])
    q8_imp = SelectField("Importanza (1-6)", choices=[(i, str(i)) for i in range(1,7)], coerce=int, validators=[DataRequired()])
    q9_req = SelectField("9. Tempestività risposta alle NC (< 7 gg) — Requisito (1-5)", choices=[(i, str(i)) for i in range(1,6)], coerce=int, validators=[DataRequired()])
    q9_imp = SelectField("Importanza (1-6)", choices=[(i, str(i)) for i in range(1,7)], coerce=int, validators=[DataRequired()])
    q10_req = SelectField("10. Qualità delle forniture — Requisito (1-5)", choices=[(i, str(i)) for i in range(1,6)], coerce=int, validators=[DataRequired()])
    q10_imp = SelectField("Importanza (1-6)", choices=[(i, str(i)) for i in range(1,7)], coerce=int, validators=[DataRequired()])
    note = TextAreaField("Note", validators=[Optional()])
    submit = SubmitField("Salva qualifica")
