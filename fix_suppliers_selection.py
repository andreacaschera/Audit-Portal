#!/usr/bin/env python3
"""
Fix suppliers dropdown in 'Richiedi manutenzione' to show ONLY qualified suppliers by type.
- Replaces the suppliers query with: Fornitore.query.filter_by(tipologia=tipo_sel).filter(Fornitore.qualifiche.any())
- Ensures the template render passes tipo_sel.
- Does NOT touch anything else.
Creates a timestamped backup of app.py in the same folder.
Usage:
  python3 fix_suppliers_selection.py /path/to/project  # the folder that contains app.py
"""
import sys, os, re, datetime

def main(root):
    app_path = os.path.join(root, "app.py")
    if not os.path.isfile(app_path):
        print("ERRORE: non trovo app.py in", root)
        sys.exit(2)

    with open(app_path, "r", encoding="utf-8") as f:
        src = f.read()

    orig = src
    changed = False

    # 1) Replace suppliers query with relationship-based filter (works without importing FornitoreQualifica)
    rel_query = ("fornitori = [x.nome for x in Fornitore.query"
                 ".filter_by(tipologia=tipo_sel)"
                 ".filter(Fornitore.qualifiche.any())"
                 ".order_by(Fornitore.nome).all()]")

    patterns = [
        r"fornitori\s*=\s*\[\s*f\.nome\s+for\s+f\s+in\s+db\.session\.query\(Fornitore\).*?\.all\(\)\s*\]",
        r"fornitori\s*=\s*\[\s*x\.nome\s+for\s+x\s+in\s+Fornitore\.query\.filter_by\(tipologia=tipo_sel\)\.order_by\(Fornitore\.nome\)\.all\(\)\s*\]",
        r"fornitori\s*=\s*\[\s*x\.nome\s+for\s+x\s+in\s+Fornitore\.query\.filter_by\(tipologia=tipo_sel\)\.filter\(Fornitore\.qualifiche\.any\(\)\)\.order_by\(Fornitore\.nome\)\.all\(\)\s*\]",
    ]
    replaced = False
    for pat in patterns:
        if re.search(pat, src, flags=re.S):
            src = re.sub(pat, rel_query, src, flags=re.S)
            changed = True
            replaced = True
            break

    # 2) Ensure tipo_sel is passed to template
    if 'render_template("manutenzione.html", fornitori=fornitori)' in src:
        src = src.replace('render_template("manutenzione.html", fornitori=fornitori)',
                          'render_template("manutenzione.html", fornitori=fornitori, tipo_sel=tipo_sel)')
        changed = True

    if changed:
        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = app_path + f".backup_{stamp}"
        with open(backup, "w", encoding="utf-8") as f:
            f.write(orig)
        with open(app_path, "w", encoding="utf-8") as f:
            f.write(src)
        print("Patch applicata. Backup creato:", backup)
    else:
        print("Nessuna modifica necessaria (sembra già a posto).")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python3 fix_suppliers_selection.py /percorso/alla/cartella/progetto")
        sys.exit(1)
    main(sys.argv[1])
