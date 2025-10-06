#!/usr/bin/env python3
import sys
import os
import re
import datetime

def ensure_imports(src: str):
    changed = False
    if "from sqlalchemy import func" not in src:
        idx = src.find("from flask import")
        if idx != -1:
            nl = src.find("\n", idx)
            if nl != -1:
                src = src[:nl+1] + "from sqlalchemy import func\n" + src[nl+1:]
            else:
                src = src + "\nfrom sqlalchemy import func\n"
        else:
            src = "from sqlalchemy import func\n" + src
        changed = True

    if "from models import FornitoreQualifica" not in src:
        m = re.search(r'^(from\s+models\s+import[^\n]*\n)', src, flags=re.M)
        if m:
            pos = m.end()
            src = src[:pos] + "from models import FornitoreQualifica\n" + src[pos:]
        else:
            src = "from models import FornitoreQualifica\n" + src
        changed = True
    return src, changed

def harden_tipo_sel(src: str):
    new_src, n = re.subn(
        r'tipo_sel\s*=\s*request\.args\.get\("tipo",\s*""\)',
        'tipo_sel = (request.args.get("tipo") or request.form.get("tipo") or "").strip().lower()',
        src
    )
    return new_src, bool(n)

def inject_supplier_block(src: str):
    join_query = (
        "fornitori = [f.nome for f in db.session.query(Fornitore)\n"
        "                       .join(FornitoreQualifica, FornitoreQualifica.fornitore_id == Fornitore.id)\n"
        "                       .filter(func.lower(Fornitore.tipologia) == tipo_sel)\n"
        "                       .distinct()\n"
        "                       .order_by(Fornitore.nome)\n"
        "                       .all()]"
    )
    block = (
        "\n        # --- fornitori qualificati (JOIN + fallback) ---\n"
        "        fornitori = []\n"
        "        if tipo_sel in (\"elettrica\", \"meccanica\"):\n"
        "            base_q = db.session.query(Fornitore).join(FornitoreQualifica, FornitoreQualifica.fornitore_id == Fornitore.id).distinct()\n"
        "            rows = base_q.filter(func.lower(Fornitore.tipologia) == tipo_sel).order_by(Fornitore.nome).all()\n"
        "            if not rows:\n"
        "                rows = base_q.filter(func.lower(Fornitore.tipologia).like(tipo_sel + \"%\")).order_by(Fornitore.nome).all()\n"
        "            if not rows:\n"
        "                rows = base_q.order_by(Fornitore.nome).all()\n"
        "            fornitori = [f.nome for f in rows]\n"
    )
    route_pat = re.compile(r"(@app\.route\(['\"]/manutenzione['\"] .*?def\s+richiedi_manutenzione\(\):)(.*?)(@app\.route\(|\Z)", re.S)
    m = route_pat.search(src)
    if not m:
        return src, False
    body = m.group(2)

    if "fornitori =" in body:
        patterns = [
            r"fornitori\s*=\s*\[\s*x\.nome\s+for\s+x\s+in\s+Fornitore\.query\.filter_by\(tipologia=tipo_sel\)\.order_by\(Fornitore\.nome\)\.all\(\)\s*\]",
            r"fornitori\s*=\s*\[\s*x\.nome\s+for\s+x\s+in\s+Fornitore\.query\.filter_by\(tipologia=tipo_sel\)\.filter\(Fornitore\.qualifiche\.any\(\)\)\.order_by\(Fornitore\.nome\)\.all\(\)\s*\]",
            r"fornitori\s*=\s*\[\s*f\.nome\s+for\s+f\s+in\s+db\.session\.query\(Fornitore\).*?\.all\(\)\s*\]",
        ]
        replaced = False
        for pat in patterns:
            if re.search(pat, body, flags=re.S):
                body = re.sub(pat, join_query, body, flags=re.S)
                replaced = True
                break
        if not replaced:
            body = re.sub(r"(return\s+render_template\(\s*\"manutenzione\.html\"[^\)]*\))", block + r"\1", body, flags=re.S)
    else:
        body = re.sub(r"(return\s+render_template\(\s*\"manutenzione\.html\"[^\)]*\))", block + r"\1", body, flags=re.S)

    new_src = src[:m.start(2)] + body + src[m.end(2):]
    return new_src, True

def ensure_render_params(src: str):
    return src.replace(
        'return render_template("manutenzione.html", fornitori=fornitori)',
        'return render_template("manutenzione.html", fornitori=fornitori, tipo_sel=tipo_sel)'
    )

def main():
    if len(sys.argv) != 2:
        print("Uso: python3 apply_patch_min2.py /percorso/alla/cartella/progetto")
        sys.exit(1)
    root = sys.argv[1]
    app_path = os.path.join(root, "app.py")
    if not os.path.isfile(app_path):
        print("ERRORE: non trovo app.py in", root)
        sys.exit(2)

    src = open(app_path, "r", encoding="utf-8").read()
    orig = src

    any_change = False
    src, ch = ensure_imports(src); any_change = any_change or ch
    src, ch = harden_tipo_sel(src); any_change = any_change or ch
    src, ch = inject_supplier_block(src); any_change = any_change or ch
    src = ensure_render_params(src)

    if any_change:
        backup = app_path + ".backup_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        open(backup, "w", encoding="utf-8").write(orig)
        open(app_path, "w", encoding="utf-8").write(src)
        print("Patch applicata. Backup:", backup)
    else:
        print("Nessuna modifica applicata (già allineato).")

if __name__ == "__main__":
    main()
