"""Bangun AgroTrace_Kopi_Dashboard.html (satu berkas, tanpa instalasi).
BASE_URL: bila dashboard sudah dihosting (mis. GitHub Pages), isi alamatnya agar QR membuka halaman batch langsung."""
import json, io, base64, os, qrcode, plotly
BASE_URL = ""
d = json.load(open("data/paspor.json"))
for p in d:
    b = io.BytesIO(); qrcode.make((BASE_URL + "#" + p["fg_id"]) if BASE_URL else "AGROTRACE|" + p["fg_id"], box_size=5, border=2).save(b, format="PNG")
    p["qr"] = base64.b64encode(b.getvalue()).decode()
pjs = open(os.path.join(os.path.dirname(plotly.__file__), "package_data", "plotly.min.js")).read()
h = open("scripts/template.html").read().replace("/*PLOTLY*/", pjs).replace("/*BASE*/", BASE_URL).replace("/*DATA*/[]", json.dumps(d, ensure_ascii=False))
open("AgroTrace_Kopi_Dashboard.html", "w").write(h); print(len(h)//1024, "KB")
