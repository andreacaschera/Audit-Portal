from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# --- ENTITY MODELS ---

class Audit(db.Model):
    __tablename__ = "audits"
    id = db.Column(db.Integer, primary_key=True)
    titolo = db.Column(db.String(200), nullable=False)
    codice = db.Column(db.String(50), unique=True, nullable=False)
    data_audit = db.Column(db.Date, nullable=False)
    cliente = db.Column(db.String(200), nullable=True)
    sede = db.Column(db.String(200), nullable=True)
    norma = db.Column(db.String(100), nullable=True)  # es: ISO 9001, ISO 37001, UNI/PdR 125
    stato = db.Column(db.String(50), default="In corso")  # In corso, Chiuso, Pianificato
    extra = db.Column(db.Text, nullable=True)  # JSON string per campi dinamici
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    non_conformita = db.relationship("NonConformita", backref="audit", cascade="all, delete-orphan")
    azioni = db.relationship("AzioneCorrettiva", backref="audit", cascade="all, delete-orphan")

    def get_extra_dict(self):
        import json
        try:
            return json.loads(self.extra) if self.extra else {}
        except Exception:
            return {}

class NonConformita(db.Model):
    __tablename__ = "non_conformita"
    id = db.Column(db.Integer, primary_key=True)
    audit_id = db.Column(db.Integer, db.ForeignKey("audits.id"), nullable=False)
    codice = db.Column(db.String(50), nullable=False)
    descrizione = db.Column(db.Text, nullable=False)
    gravita = db.Column(db.String(20), nullable=False)  # Minore, Maggiore, Critica
    categoria = db.Column(db.String(100), nullable=True)
    rilevata_da = db.Column(db.String(120), nullable=True)
    data_apertura = db.Column(db.Date, default=datetime.utcnow)
    stato = db.Column(db.String(20), default="Aperta")  # Aperta, In corso, Chiusa

    azioni = db.relationship("AzioneCorrettiva", backref="non_conformita", cascade="all, delete-orphan")

class AzioneCorrettiva(db.Model):
    __tablename__ = "azioni_correttive"
    id = db.Column(db.Integer, primary_key=True)
    audit_id = db.Column(db.Integer, db.ForeignKey("audits.id"), nullable=False)
    nc_id = db.Column(db.Integer, db.ForeignKey("non_conformita.id"), nullable=True)
    azione = db.Column(db.Text, nullable=False)
    responsabile = db.Column(db.String(120), nullable=True)
    data_scadenza = db.Column(db.Date, nullable=True)
    stato = db.Column(db.String(20), default="Aperta")  # Aperta, In corso, Chiusa
    efficacia = db.Column(db.String(50), nullable=True)  # Efficace, Non Efficace, Da Verificare

# --- DYNAMIC FIELDS (no schema change required) ---

class CustomField(db.Model):
    __tablename__ = "custom_fields"
    id = db.Column(db.Integer, primary_key=True)
    entity = db.Column(db.String(50), nullable=False)  # 'audit', 'nc', 'azione'
    name = db.Column(db.String(100), nullable=False)
    label = db.Column(db.String(200), nullable=False)
    field_type = db.Column(db.String(30), nullable=False)  # text, textarea, integer, decimal, date, select
    options = db.Column(db.Text, nullable=True)  # JSON list per select
    required = db.Column(db.Boolean, default=False)

class CustomValue(db.Model):
    __tablename__ = "custom_values"
    id = db.Column(db.Integer, primary_key=True)
    field_id = db.Column(db.Integer, db.ForeignKey("custom_fields.id"), nullable=False)
    entity = db.Column(db.String(50), nullable=False)  # 'audit', 'nc', 'azione'
    entity_id = db.Column(db.Integer, nullable=False)
    value = db.Column(db.Text, nullable=True)

    field = db.relationship("CustomField", backref="values")


class ChecklistItem(db.Model):
    __tablename__ = "checklist_items"
    id = db.Column(db.Integer, primary_key=True)
    audit_id = db.Column(db.Integer, db.ForeignKey("audits.id"), nullable=False)
    descrizione = db.Column(db.String(500), nullable=False)
    esito = db.Column(db.String(20), default="Aperta")  # Conforme, Non conforme, Non applicabile, Aperta (default)
    ordine = db.Column(db.Integer, default=0)
    note = db.Column(db.Text, nullable=True)

    audit = db.relationship("Audit", backref=db.backref("checklist", cascade="all, delete-orphan"))


class Fornitore(db.Model):
    __tablename__ = "fornitori"
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False)
    telefono = db.Column(db.String(50), nullable=True)
    contatto = db.Column(db.String(200), nullable=True)
    tipologia = db.Column(db.String(50), nullable=False)  # "elettrica" | "meccanica" | "servizi"
    indirizzo = db.Column(db.String(300), nullable=True)
    citta = db.Column(db.String(120), nullable=True)

    def __repr__(self):
        return f"<Fornitore {self.nome} ({self.tipologia})>"


class InterventoManutenzione(db.Model):
    __tablename__ = "interventi_manutenzione"
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(20), nullable=False)  # "elettrica" | "meccanica" | "servizi"
    descrizione = db.Column(db.Text, nullable=False)
    richiedente = db.Column(db.String(200), nullable=False)
    centro = db.Column(db.String(200), nullable=False)
    fornitore = db.Column(db.String(200), nullable=True)
    destinatario = db.Column(db.String(200), nullable=True)
    data_intervento = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default="Non assegnato")  # "Eseguito" | "Assegnato" | "Non assegnato"



class FornitoreQualifica(db.Model):
    __tablename__ = "fornitore_qualifiche"
    id = db.Column(db.Integer, primary_key=True)
    fornitore_id = db.Column(db.Integer, db.ForeignKey("fornitori.id"), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    # Per ogni domanda: requisito (1-5), importanza (1-6)
    q1_req = db.Column(db.Integer, nullable=True); q1_imp = db.Column(db.Integer, nullable=True)
    q2_req = db.Column(db.Integer, nullable=True); q2_imp = db.Column(db.Integer, nullable=True)
    q3_req = db.Column(db.Integer, nullable=True); q3_imp = db.Column(db.Integer, nullable=True)
    q4_req = db.Column(db.Integer, nullable=True); q4_imp = db.Column(db.Integer, nullable=True)
    q5_req = db.Column(db.Integer, nullable=True); q5_imp = db.Column(db.Integer, nullable=True)
    q6_req = db.Column(db.Integer, nullable=True); q6_imp = db.Column(db.Integer, nullable=True)
    q7_req = db.Column(db.Integer, nullable=True); q7_imp = db.Column(db.Integer, nullable=True)
    q8_req = db.Column(db.Integer, nullable=True); q8_imp = db.Column(db.Integer, nullable=True)
    q9_req = db.Column(db.Integer, nullable=True); q9_imp = db.Column(db.Integer, nullable=True)
    q10_req = db.Column(db.Integer, nullable=True); q10_imp = db.Column(db.Integer, nullable=True)
    note = db.Column(db.Text, nullable=True)

    fornitore = db.relationship("Fornitore", backref=db.backref("qualifiche", lazy="dynamic"))

    @property
    def scores(self):
        pairs = [
            (self.q1_req, self.q1_imp),
            (self.q2_req, self.q2_imp),
            (self.q3_req, self.q3_imp),
            (self.q4_req, self.q4_imp),
            (self.q5_req, self.q5_imp),
            (self.q6_req, self.q6_imp),
            (self.q7_req, self.q7_imp),
            (self.q8_req, self.q8_imp),
            (self.q9_req, self.q9_imp),
            (self.q10_req, self.q10_imp),
        ]
        scores = []
        for r, i in pairs:
            if r and i:
                scores.append(int(r) * int(i))
        return scores

    @property
    def final_score(self):
        sc = self.scores
        return round(sum(sc) / len(sc), 2) if sc else 0.0
