#!/usr/bin/env python3
"""
Hardens the 'Richiedi manutenzione' view to avoid Internal Server Error and
ensures suppliers dropdown lists only qualified suppliers by type.
- Adds a robust fallback for tipo_sel retrieval (args or form)
- Wraps supplier query in try/except and defaults to []
- Ensures template receives both 'fornitori' and 'tipo_sel'
- Leaves the rest of app.py untouched; creates a timestamped backup
Usage:
  python3 fix_richiesta_manutenzione.py /path/to/project  # folder that contains app.py
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

    # 1) Ensure robust tipo_sel retrieval (args OR form), near where tipo_sel is set
    # Replace occurrences of: tipo_sel = request.args.get("tipo", "")
    src2, n1 = re.subn(r'tipo_sel\s*=\s*request\.args\.get\("tipo",\s*""\)',
                       'tipo_sel = (request.args.get("tipo") or request.form.get("tipo") or "")',
                       src)
    if n1:
        src = src2
        changed = True

    # 2) Ensure suppliers query uses qualified-only and is protected
    # First, normalize previous query into a marker we can replace
    qualified_query = ('fornitori = [x.nome for x in Fornitore.query'
                       '.filter_by(tipologia=tipo_sel)'
                       '.filter(Fornitore.qualifiche.any())'
                       '.order_by(Fornitore.nome).all()]')

    patterns = [
        r'fornitori\s*=\s*\[\s*x\.nome\s+for\s+x\s+in\s+Fornitore\.query\.filter_by\(tipologia=tipo_sel\)\.order_by\(Fornitore\.nome\)\.all\(\)\s*\]',
        r'fornitori\s*=\s*\[\s*f\.nome\s+for\s+f\s+in\s+db\.session\.query\(Fornitore\).*?\.all\(\)\s*\]',
        r'fornitori\s*=\s*\[\s*x\.nome\s+for\s+x\s+in\s+Fornitore\.query\.filter_by\(tipologia=tipo_sel\)\.filter\(Fornitore\.qualifiche\.any\(\)\)\.order_by\(Fornitore\.nome\)\.all\(\)\s*\]',
    ]
    replaced = False
    for pat in patterns:
        if re.search(pat, src, flags=re.S):
            src = re.sub(pat, qualified_query, src, flags=re.S)
            changed = True
            replaced = True
            break

    # 3) Wrap the "build fornitori + return render_template(...)" area in a try/except
    # Replace any 'return render_template("manutenzione.html", ...)' within the manutenzione view
    # by injecting a safe block before returning.
    safe_block = (
        '        # Safe build of suppliers list\n'
        '        fornitori = []\n'
        '        try:\n'
        '            if tipo_sel in ("elettrica", "meccanica"):\n'
        '                fornitori = [x.nome for x in Fornitore.query\n'
        '                    .filter_by(tipologia=tipo_sel)\n'
        '                    .filter(Fornitore.qualifiche.any())\n'
        '                    .order_by(Fornitore.nome).all()]\n'
        '        except Exception:\n'
        '            fornitori = []\n'
        '\n'
        '        return render_template("manutenzione.html", fornitori=fornitori, tipo_sel=tipo_sel)\n'
    )

    # Find the manutenzione route and replace the tail that returns the template
    route_pat = re.compile(r"(@app\.route\([\"']\/manutenzione[\"'].*?def\s+richiedi_manutenzione\(\):)(.*?)(@app\.route\(|\Z)", re.S)
    m = route_pat.search(src)
    if m:
        body = m.group(2)
        # Replace the last return render_template(...) with our safe block
        body2 = re.sub(r"return\s+render_template\(\s*\"manutenzione\.html\".*?\)\s*", safe_block, body, flags=re.S)
        if body2 != body:
            src = src[:m.start(2)] + body2 + src[m.end(2):]
            changed = True

    # 4) Ensure at least one render passes tipo_sel if not caught
    src = src.replace('return render_template("manutenzione.html", fornitori=fornitori)',
                      'return render_template("manutenzione.html", fornitori=fornitori, tipo_sel=tipo_sel)')

    if changed:
        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = app_path + f".backup_{stamp}"
        with open(backup, "w", encoding="utf-8") as f:
            f.write(orig)
        with open(app_path, "w", encoding="utf-8") as f:
            f.write(src)
        print("Patch applicata. Backup creato:", backup)
    else:
        print("Sembra già a posto. Nessuna modifica applicata.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python3 fix_richiesta_manutenzione.py /percorso/alla/cartella/progetto")
        sys.exit(1)
    main(sys.argv[1])
