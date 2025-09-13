# Pacchetto completo - Formazione + Qualifica Fornitori

Questa cartella **V3** contiene tutti i file già modificati:
- `app.py` aggiornato con import e registrazione dei blueprint
- `templates/base.html` con due voci di menu in più
- nuovi file: `training.py`, `training_models.py`, `training_forms.py`, `suppliers.py`
- nuovi template in `templates/formazione/` e `templates/qualifica_fornitori.html`

## Primo avvio
1. Attiva il venv e installa i requirements (già presenti).
2. Crea le nuove tabelle:
```
python - <<'PY'
from app import app
from models import db
import training_models
with app.app_context():
    db.create_all()
print("Tabelle create/aggiornate.")
PY
```
3. Avvia l'app e prova dal menu **Formazione**.

Materiali corsi: `instance/training_materials/`  
Attestati PDF: `instance/certificates/`
