#!/usr/bin/env python3
import sys, os, re, datetime

def main(root):
    app_path = os.path.join(root, "app.py")
    if not os.path.isfile(app_path):
        print("ERRORE: Non trovo app.py in", root)
        sys.exit(2)

    with open(app_path, "r", encoding="utf-8") as f:
        src = f.read()

    orig = src
    changed = False

    # 1) Fix dangling import and ensure FornitoreQualifica is imported (safest: separate import line)
    if "from models import FornitoreQualifica" not in src:
        # Try to merge into existing 'from models import' line that contains Fornitore
        merged = False
        for m in re.finditer(r'^(from models import [^\n]+)$', src, re.M):
            line = m.group(1)
            if "Fornitore" in line and "FornitoreQualifica" not in line:
                # If line already uses parentheses multiline, append before closing )
                if "(" in line and ")" in line:
                    new_line = line.replace(")", ", FornitoreQualifica)")
                else:
                    new_line = line + ", FornitoreQualifica"
                src = src[:m.start()] + new_line + src[m.end():]
                merged = True
                changed = True
                break
        if not merged:
            # fall back: add a dedicated import line right after first 'from models import'
            pos = src.find("from models import")
            if pos != -1:
                nl = src.find("\n", pos)
                if nl != -1:
                    src = src[:nl+1] + "from models import FornitoreQualifica\n" + src[nl+1:]
                    changed = True
            else:
                # If no 'from models import' found, just add at top after shebang/encoding if any
                src = "from models import FornitoreQualifica\n" + src
                changed = True

    # 2) Ensure supplier query uses a JOIN on FornitoreQualifica
    join_query = (
        "fornitori = [f.nome for f in db.session.query(Fornitore)"
        ".join(FornitoreQualifica, FornitoreQualifica.fornitore_id == Fornitore.id)"
        ".filter(Fornitore.tipologia == tipo_sel)"
        ".distinct()"
        ".order_by(Fornitore.nome)"
        ".all()]"
    )
    patterns = [
        r"fornitori\s*=\s*\[\s*x\.nome\s+for\s+x\s+in\s+Fornitore\.query\.filter_by\(tipologia=tipo_sel\)\.filter\(Fornitore\.qualifiche\.any\(\)\)\.order_by\(Fornitore\.nome\)\.all\(\)\s*\]",
        r"fornitori\s*=\s*\[\s*x\.nome\s+for\s+x\s+in\s+Fornitore\.query\.filter_by\(tipologia=tipo_sel\)\.order_by\(Fornitore\.nome\)\.all\(\)\s*\]",
    ]
    for pat in patterns:
        if re.search(pat, src):
            src = re.sub(pat, join_query, src)
            changed = True
            break

    # 3) Ensure tipo_sel is passed to template
    src = src.replace(
        'return render_template("manutenzione.html", fornitori=fornitori)',
        'return render_template("manutenzione.html", fornitori=fornitori, tipo_sel=tipo_sel)'
    )

    if src != orig:
        # backup
        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = app_path + f".bak_{stamp}"
        with open(backup, "w", encoding="utf-8") as f:
            f.write(orig)
        with open(app_path, "w", encoding="utf-8") as f:
            f.write(src)
        print("Patch applicata. Backup creato:", backup)
    else:
        print("Nulla da cambiare. Il file sembra già corretto.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python3 fix_import_and_query.py /percorso/alla/cartella/progetto (quella che contiene app.py)")
        sys.exit(1)
    main(sys.argv[1])
