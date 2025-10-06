    #!/usr/bin/env python3
    import sys, os, re, datetime

    def main(root):
        app_path = os.path.join(root, "app.py")
        if not os.path.isfile(app_path):
            print("ERRORE: non trovo app.py in", root); sys.exit(2)

        src = open(app_path,"r",encoding="utf-8").read()
        orig = src
        changed = False

        # 1) import func e FornitoreQualifica
        if "from sqlalchemy import func" not in src:
            src = src.replace("from flask import", "from sqlalchemy import func
from flask import")
            changed = True
        if "from models import FornitoreQualifica" not in src:
            # inserisci dopo la prima riga 'from models import ...'
            m = re.search(r'^(from\s+models\s+import[^\n]*\n)', src, flags=re.M)
            if m:
                pos = m.end()
                src = src[:pos] + "from models import FornitoreQualifica\n" + src[pos:]
            else:
                src = "from models import FornitoreQualifica\n" + src
            changed = True

        # 2) tipo_sel robusto (GET o POST), lower
        src, n = re.subn(r'tipo_sel\s*=\s*request\.args\.get\("tipo",\s*""\)',
                         'tipo_sel = (request.args.get("tipo") or request.form.get("tipo") or "").strip().lower()', src)
        changed = changed or bool(n)

        # 3) inietto blocco di costruzione fornitori qualificati con fallback, prima del render_template
        block = (
            "\n        # --- fornitori qualificati con fallback ---\n"
            "        fornitori = []\n"
            "        if tipo_sel in (\"elettrica\", \"meccanica\"):\n"
            "            base_q = db.session.query(Fornitore)"
            ".join(FornitoreQualifica, FornitoreQualifica.fornitore_id == Fornitore.id)"
            ".distinct()\n"
            "            rows = base_q.filter(func.lower(Fornitore.tipologia) == tipo_sel)"
            ".order_by(Fornitore.nome).all()\n"
            "            if not rows:\n"
            "                rows = base_q.filter(func.lower(Fornitore.tipologia).like(tipo_sel + \"%\"))"
            ".order_by(Fornitore.nome).all()\n"
            "            if not rows:\n"
            "                rows = base_q.order_by(Fornitore.nome).all()\n"
            "            fornitori = [f.nome for f in rows]\n"
        )
        # colpisci solo la view manutenzione
        route_pat = re.compile(r"(@app\.route\(['\"]/manutenzione['\"] .*?def\s+richiedi_manutenzione\(\):)(.*?)(@app\.route\(|\Z)", re.S)
        m = route_pat.search(src)
        if m:
            body = m.group(2)
            body2 = re.sub(r"(return\s+render_template\(\s*\"manutenzione\.html\"[^\)]*\))", block + r"\1", body, flags=re.S)
            if body2 != body:
                src = src[:m.start(2)] + body2 + src[m.end(2):]
                changed = True

        # 4) assicurati che tipo_sel venga passato al template
        src = src.replace('return render_template("manutenzione.html", fornitori=fornitori)',
                          'return render_template("manutenzione.html", fornitori=fornitori, tipo_sel=tipo_sel)')

        if changed:
            backup = app_path + ".backup_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            open(backup,"w",encoding="utf-8").write(orig)
            open(app_path,"w",encoding="utf-8").write(src)
            print("Patch applicata. Backup:", backup)
        else:
            print("Nessuna modifica applicata (file già allineato).")

    if __name__ == "__main__":
        if len(sys.argv) != 2:
            print("Uso: python3 apply_patch_min.py /percorso/alla/cartella/progetto"); sys.exit(1)
        main(sys.argv[1])
