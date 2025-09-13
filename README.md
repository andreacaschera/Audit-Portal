# Audit Portal (Flask)

Portale in Python/Flask per gestire audit, non conformità e piano delle azioni correttive.
Grafica professionale (Bootstrap 5), database dinamico con **campi personalizzati** senza modificare lo schema.

## Funzioni principali
- **Menù di selezione** con 5 voci richieste.
- **Inizia nuovo audit** con campi standard + *campi personalizzati* (configurabili da *Configura campi*).
- **Elenco audit** con ricerca.
- **Seleziona audit** e pagina **Dettaglio audit**.
- **Elenco non conformità** con filtro per audit e creazione nuova NC.
- **Piano delle azioni correttive** con creazione azioni e collegamento a NC.
- **Pannello semplice** per aggiungere *Custom Fields* (senza toccare il DB).

## Requisiti
- Python 3.10+

## Setup rapido
```bash
python -m venv .venv
source .venv/bin/activate  # su Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```
Apri il browser su http://127.0.0.1:5000

## Note su "database dinamico"
- La tabella `custom_fields` ti permette di **aggiungere nuovi campi** (es. "Reparto auditato") per l'entità *audit*.
- I valori vengono salvati in `custom_values` e anche come JSON nel campo `extra` dell'audit, così puoi esportare velocemente.
- Puoi estendere lo stesso meccanismo per NC e Azioni (basta cambiare `entity='nc'` o `'azione'` nel pannello di config e usare il pattern nel form).

## Personalizzazione UI
- Cambia logo, nome azienda e nome app in `config.py`.
- Stili aggiuntivi in `static/custom.css`.
```
