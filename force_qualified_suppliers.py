#!/usr/bin/env python3
import sys, os, re, datetime

def ensure_imports(src):
    changed = False
    if "from sqlalchemy import func" not in src:
        lines = src.splitlines()
        # insert near other imports
        insert_at = 0
        for i,ln in enumerate(lines[:60]):
            if "from flask" in ln or "from sqlalchemy" in ln or "from werkzeug" in ln:
                insert_at = i+1
        lines.insert(insert_at, "from sqlalchemy import func")
        src = "\n".join(lines)
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

def patch_view(src):
    changed = False
    # robust tipo_sel
    src2, n = re.subn(r'tipo_sel\s*=\s*request\.args\.get\("tipo",\s*""\)',
                      'tipo_sel = (request.args.get("tipo") or request.form.get("tipo") or "").strip().lower()',
                      src)
    if n:
        src = src2
        changed = True

    # replace suppliers query
    join_query = (
        "fornitori = [f.nome for f in db.session.query(Fornitore)\n"
        "                    .join(FornitoreQualifica, FornitoreQualifica.fornitore_id == Fornitore.id)\n"
        "                    .filter(func.lower(Fornitore.tipologia) == tipo_sel)\n"
        "                    .distinct()\n"
        "                    .order_by(Fornitore.nome)\n"
        "                    .all()]"
    )
    patterns = [
        r"fornitori\s*=\s*\[\s*x\.nome\s+for\s+x\s+in\s+Fornitore\.query\.filter_by\(tipologia=tipo_sel\)\.order_by\(Fornitore\.nome\)\.all\(\)\s*\]",
        r"fornitori\s*=\s*\[\s*x\.nome\s+for\s+x\s+in\s+Fornitore\.query\.filter_by\(tipologia=tipo_sel\)\.filter\(Fornitore\.qualifiche\.any\(\)\)\.order_by\(Fornitore\.nome\)\.all\(\)\s*\]",
        r"fornitori\s*=\s*\[\s*f\.nome\s+for\s+f\s+in\s+db\.session\.query\(Fornitore\).*?\.all\(\)\s*\]",
    ]
    replaced = False
    for pat in patterns:
        if re.search(pat, src, flags=re.S):
            src = re.sub(pat, join_query, src, flags=re.S)
            changed = True
            replaced = True
            break

    # if no pattern matched, inject block before render
    if not replaced:
        route_pat = re.compile(r"(@app\.route\([\"']\/manutenzione[\"'].*?def\s+richiedi_manutenzione\(\):)(.*?)(@app\.route\(|\Z)", re.S)
        m = route_pat.search(src)
        if m:
            body = m.group(2)
            safe_block = (
                "\n        # --- suppliers (qualified only) ---\n"
                "        fornitori = []\n"
                "        if tipo_sel in (\"elettrica\",\"meccanica\"):\n"
                "            " + join_query + "\n"
            )
            body2 = re.sub(r"(return\s+render_template\(\s*\"manutenzione\.html\"[^\)]*\))",
                           safe_block + r"\1",
                           body, flags=re.S)
            if body2 != body:
                src = src[:m.start(2)] + body2 + src[m.end(2):]
                changed = True

    # ensure render passes tipo_sel
    src = src.replace('return render_template("manutenzione.html", fornitori=fornitori)',
                      'return render_template("manutenzione.html", fornitori=fornitori, tipo_sel=tipo_sel)')
    return src, changed

def main(root):
    app_path = os.path.join(root, "app.py")
    if not os.path.isfile(app_path):
        print("ERRORE: non trovo app.py in", root)
        sys.exit(2)

    src = open(app_path,"r",encoding="utf-8").read()
    orig = src

    src, _ = ensure_imports(src)
    src, _ = patch_view(src)

    if src != orig:
        backup = app_path + ".backup_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        open(backup,"w",encoding="utf-8").write(orig)
        open(app_path,"w",encoding="utf-8").write(src)
        print("Patch applicata. Backup:", backup)
    else:
        print("Nessuna modifica necessaria.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python3 force_qualified_suppliers.py /percorso/alla/cartella/progetto")
        sys.exit(1)
    main(sys.argv[1])
