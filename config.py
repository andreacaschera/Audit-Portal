import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "cambia-questa-chiave-super-segreta")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "sqlite:///" + os.path.join(os.path.dirname(__file__), "instance", "app.db")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_TIME_LIMIT = None
    # Branding
    APP_NAME = "Audit Portal"
    COMPANY_NAME = "Tua Azienda"
    COMPANY_LOGO = "/static/logo.svg"

    # Policy: consente eliminazione di utenti con ruolo Supervisor (0=No, 1=Sì)
    ALLOW_SUPERVISOR_DELETION = os.environ.get("ALLOW_SUPERVISOR_DELETION", "0") in ("1", "true", "True")
