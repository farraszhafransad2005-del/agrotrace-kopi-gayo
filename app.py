"""AgroTrace Carbon Passport - Kopi Arabika Gayo Natural.
Frontend: Streamlit. Backend/data: MongoDB Atlas (database agrotrace_kopi, koleksi paspor).
Tanpa mongo_uri, aplikasi memakai data/paspor.json (mode demo)."""
import io, json, os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import qrcode
import streamlit as st

st.set_page_config(page_title="AgroTrace Kopi Gayo", page_icon="☕", layout="wide")
ESP, ROAST, RED, CREMA, LEAF = "#2E1A0E", "#6F4E37", "#A4442A", "#C8A27A", "#5E7C4A"
st.markdown(f"""<style>
.stApp{{background:#F6EEE1}} h1,h2,h3{{color:{ESP}}}
.hero{{background:linear-gradient(135deg,{ESP},{ROAST});color:#fff;padding:22px 26px;border-radius:14px;margin-bottom:12px}}
.hero h1{{color:#fff;margin:0;font-size:28px}} .hero p{{margin:4px 0 0;opacity:.85}}
.badge-ok{{background:#DDEEDD;color:#3E7C4F;padding:4px 12px;border-radius:20px;font-weight:700}}
.badge-bad{{background:#F8DAD5;color:#C0392B;padding:4px 12px;border-radius:20px;font-weight:700}}
.steps{{display:flex;justify-content:space-between;margin:14px 0}} .stp{{text-align:center;flex:1;font-size:13px;color:#7a6757}}
.dot{{width:42px;height:42px;border-radius:50%;background:{CREMA};color:{ESP};display:flex;align-items:center;justify-content:center;margin:0 auto 4px;font-weight:700}}
.dot.on{{background:{RED};color:#fff;outline:3px solid {ESP}}}
.note{{background:#F3E4CC;border-left:5px solid {RED};padding:10px 14px;border-radius:6px;font-size:14px}}
div[data-testid="stMetric"]{{background:#FFFBF4;border:1px solid #E5D6C0;border-left:6px solid {RED};padding:10px 14px;border-radius:12px}}
</style>""", unsafe_allow_html=True)
CATATAN = ("Skor intensitas adalah proxy proses relatif antar batch (lama jemur 40%, durasi roasting 30%, susut roasting 30%) "
           "berdasarkan asumsi tim. Nilai ini bukan besaran emisi karbon.")
TAHAP = ["Panen", "Pascapanen", "Green bean", "Roasting", "Kemas", "Distribusi"]


@st.cache_data(ttl=300, show_spinner="Memuat data paspor...")
def muat():
    uri = None
    try:
        uri = st.secrets["mongo_uri"]
    except Exception:
        uri = os.environ.get("MONGO_URI")
    if uri:
        from pymongo import MongoClient
        db = MongoClient(uri, serverSelectionTimeoutMS=8000)["agrotrace_kopi"]
        return list(db["paspor"].find({}, {"_id": 0})), "MongoDB Atlas"
    with open("data/paspor.json", encoding="utf-8") as f:
        return json.load(f), "berkas lokal data/paspor.json (mode demo, belum terhubung MongoDB)"


def audit_ulang(p):
    """Hitung audit dari data dokumen saat ini (bukan membaca hasil lama), sama dengan scripts/2_buat_paspor.py."""
    from datetime import date
    g, rs, hs = p["green"], p["roasting"], p["panen"]
    kosong = lambda v: v is None or (isinstance(v, float) and pd.isna(v))
    out = []
    add = lambda r, ok, m: out.append({"aturan": r, "lulus": bool(ok), "catatan": m})
    add("Kadar air green bean <= 12,5%", g["kadar_air_green_persen"] <= 12.5, f"{g['green_id']}: {g['kadar_air_green_persen']}%")
    bad = [r for r in rs if not 10 <= r["susut_persen"] <= 20]
    add("Susut roasting 10-20%", not bad, "semua batch wajar" if not bad else "; ".join(f"{r['roast_id']}: {r['susut_persen']}%" for r in bad))
    kg = sum(r["berat_sangrai_kg"] for r in rs); pack = p["jumlah_kemasan"] * 0.2
    add("Neraca massa: berat kemasan <= berat sangrai", pack <= kg + 1e-6, f"kemasan {pack:.1f} kg vs sangrai {kg:.1f} kg")
    miss = [c for c in ["ceri_merah_persen", "ceri_apung_persen", "kadar_air_kering_persen", "lama_jemur_hari"] if any(kosong(h.get(c)) for h in hs)]
    add("Data lot panen lengkap", not miss, "lengkap" if not miss else "kosong: " + ", ".join(miss))
    d = date.fromisoformat
    ok = all(d(a) <= d(b) for a, b in [(max(h["tgl_selesai_jemur"] for h in hs), g["tgl_hulling"]), (g["tgl_hulling"], min(r["tgl_roasting"] for r in rs)),
             (max(r["tgl_roasting"] for r in rs), p["tgl_kemas"]), (p["tgl_kemas"], p["tgl_kirim"]), (p["tgl_kemas"], p["tgl_kedaluwarsa"])])
    add("Urutan tanggal logis (panen > jemur > hulling > roasting > kemas > kirim)", ok, "berurutan" if ok else "ada tanggal yang mendahului tahap sebelumnya")
    add("Rendemen ceri ke green bean 15-25%", 15 <= g["rendemen_persen"] <= 25, f"{g['rendemen_persen']}%")
    return out


try:
    DATA, SUMBER = muat()
except Exception as e:
    st.markdown('<div class="hero"><h1>AgroTrace Carbon Passport</h1></div>', unsafe_allow_html=True)
    st.error("Data gagal dimuat dari MongoDB. Periksa koneksi internet, isi mongo_uri di secrets, "
             "dan Network Access di Atlas (Allow Access from Anywhere), lalu muat ulang halaman.")
    st.caption(f"Detail teknis: {type(e).__name__}")
    st.stop()
if not DATA:
    st.error("Koleksi paspor kosong. Jalankan: python scripts/4_unggah_mongodb.py \"<connection string>\"")
    st.stop()
for _d in DATA:  # audit dihitung ulang dari data terkini
    _d["audit"] = audit_ulang(_d)
    _d["status_audit"] = "Lulus" if all(a["lulus"] for a in _d["audit"]) else "Perlu ditinjau"
DATA = sorted(DATA, key=lambda d: d["fg_id"])
POR = {d["fg_id"]: d for d in DATA}

st.markdown('<div class="hero"><h1>☕ AgroTrace Carbon Passport</h1>'
            '<p>Telusuri kopi Arabika Gayo dari kebun sampai kemasan</p></div>', unsafe_allow_html=True)
st.caption(f"Sumber data: {SUMBER} · Data simulasi untuk prototipe, bukan data lot nyata.")

n = lambda v, u="": "tidak tercatat" if v is None or (isinstance(v, float) and pd.isna(v)) else (f"{v:,.1f}{u}".replace(",", "X").replace(".", ",").replace("X", "."))
tg = lambda s: pd.to_datetime(s).strftime("%d %b %Y") if s else "-"


def qr_png(fg_id):
    base = os.environ.get("BASE_URL", "")
    isi = f"{base}?batch={fg_id}" if base else f"AGROTRACE|{fg_id}"
    b = io.BytesIO(); qrcode.make(isi, box_size=6, border=2).save(b, format="PNG"); return b.getvalue()


tab_t, tab_r, tab_a, tab_p = st.tabs(["🔎 Telusuri Batch", "📊 Ringkasan", "✅ Audit", "📖 Panduan"])

with tab_t:
    awal = st.query_params.get("batch", DATA[0]["fg_id"])
    ids = list(POR)
    kode = st.selectbox("Pilih atau ketik kode batch (contoh: FG-GYO-2603-001)", ids,
                        index=ids.index(awal) if awal in ids else 0)
    P = POR[kode]; g = P["green"]; rs = P["roasting"]; hs = P["panen"]
    ok = P["status_audit"] == "Lulus"
    petani = sorted({h["petani"] for h in hs})
    kiri, kanan = st.columns([4, 1])
    with kiri:
        st.markdown(f'<span class="{"badge-ok" if ok else "badge-bad"}">Audit: {P["status_audit"]}</span>', unsafe_allow_html=True)
        st.subheader(P["fg_id"]); st.caption(P["produk"])
        rata_jemur = sum(h["lama_jemur_hari"] for h in hs) / len(hs)
        st.markdown(f"Batch ini berisi **{P['jumlah_kemasan']:,} kemasan**, dikemas {tg(P['tgl_kemas'])}. Kopinya dipanen dari "
                    f"**{len(petani)} petani** di {' dan '.join(sorted({h['kabupaten'] for h in hs}))}, dijemur rata-rata "
                    f"{rata_jemur:.1f} hari, lalu disangrai pada {len(rs)} batch roasting. Skor cupping green bean **{g['skor_cupping']}**.")
        gagal = [a for a in P["audit"] if not a["lulus"]]
        if gagal:
            st.markdown('<div class="note"><b>Temuan audit:</b> ' + "; ".join(f"{a['aturan']} ({a['catatan']})" for a in gagal) + "</div>", unsafe_allow_html=True)
    with kanan:
        png = qr_png(P["fg_id"]); st.image(png, caption="QR Passport", width=140)
        st.download_button("Unduh QR", png, f"qr_{P['fg_id']}.png", "image/png")
    tahap = st.radio("Lihat tahap", TAHAP, horizontal=True, label_visibility="collapsed")
    i = TAHAP.index(tahap)
    st.markdown('<div class="steps">' + "".join(f'<div class="stp"><div class="dot{" on" if j == i else ""}">{j+1}</div>{t}</div>' for j, t in enumerate(TAHAP)) + "</div>", unsafe_allow_html=True)
    if i == 0:
        st.markdown("##### 1. Panen: asal petani dan kebun")
        st.dataframe(pd.DataFrame(hs)[["harvest_id", "petani", "desa", "kabupaten", "varietas", "ketinggian_mdpl", "tgl_panen", "berat_ceri_kg", "ceri_merah_persen"]], hide_index=True)
    elif i == 1:
        st.markdown("##### 2. Pascapanen: penjemuran natural")
        st.dataframe(pd.DataFrame(hs)[["harvest_id", "metode_jemur", "tgl_mulai_jemur", "tgl_selesai_jemur", "lama_jemur_hari", "kadar_air_kering_persen", "ceri_apung_persen"]], hide_index=True)
    elif i == 2:
        st.markdown(f"##### 3. Green bean: {g['green_id']}")
        c = st.columns(3)
        for k, (l, v) in enumerate([("Tanggal hulling", tg(g["tgl_hulling"])), ("Berat green bean", n(g["berat_green_kg"], " kg")), ("Rendemen dari ceri", n(g["rendemen_persen"], "%")),
                                     ("Ukuran ayakan", g["ukuran_ayakan"]), ("Cacat per 300 g", g["cacat_per_300g"]), ("Kadar air", n(g["kadar_air_green_persen"], "%")),
                                     ("Skor cupping", g["skor_cupping"]), ("Gudang", g["gudang"]), ("Lama simpan", f"{g['lama_simpan_hari']} hari")]):
            c[k % 3].metric(l, v)
    elif i == 3:
        st.markdown(f"##### 4. Roasting: {len(rs)} batch, {sum(r['berat_sangrai_kg'] for r in rs):.1f} kg kopi sangrai")
        st.dataframe(pd.DataFrame(rs)[["roast_id", "tgl_roasting", "mesin", "level", "muatan_green_kg", "suhu_charge_c", "suhu_drop_c", "durasi_menit", "susut_persen", "berat_sangrai_kg"]], hide_index=True)
    elif i == 4:
        st.markdown("##### 5. Kemas: barang jadi")
        c = st.columns(3)
        for k, (l, v) in enumerate([("Kode batch", P["fg_id"]), ("Tanggal kemas", tg(P["tgl_kemas"])), ("Jumlah kemasan 200 g", f"{P['jumlah_kemasan']:,}"),
                                     ("Kedaluwarsa", tg(P["tgl_kedaluwarsa"])), ("Skor intensitas", f"{P['skor_intensitas']} ({P['kategori_intensitas']})")]):
            c[k % 3].metric(l, v)
        st.markdown(f'<div class="note">{CATATAN}</div>', unsafe_allow_html=True)
    else:
        st.markdown("##### 6. Distribusi")
        c = st.columns(3)
        c[0].metric("Tujuan", P["tujuan_distribusi"]); c[1].metric("Tanggal kirim", tg(P["tgl_kirim"])); c[2].metric("Jumlah dikirim", f"{P['jumlah_kemasan']:,} kemasan")

with tab_r:
    gl = {d["green"]["green_id"]: d["green"] for d in DATA}
    rr = {r["roast_id"]: r for d in DATA for r in d["roasting"]}
    hh = {h["harvest_id"]: h for d in DATA for h in d["panen"]}
    k = st.columns(5)
    k[0].metric("Batch barang jadi", len(DATA)); k[1].metric("Total kemasan 200 g", f"{sum(d['jumlah_kemasan'] for d in DATA):,}")
    k[2].metric("Rata-rata skor cupping", f"{sum(x['skor_cupping'] for x in gl.values())/len(gl):.1f}")
    k[3].metric("Batch lulus audit", f"{sum(d['status_audit']=='Lulus' for d in DATA)} dari {len(DATA)}"); k[4].metric("Petani terlibat", len({h['petani'] for h in hh.values()}))
    L = dict(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color=ESP), margin=dict(t=50, l=40, r=10, b=40))
    c1, c2 = st.columns(2)
    g1 = pd.DataFrame(gl.values())
    f = px.bar(g1, x="green_id", y="skor_cupping", title="Skor cupping per lot green bean", color_discrete_sequence=[ROAST]); f.update_yaxes(range=[78, 90]); f.update_layout(**L); c1.plotly_chart(f)
    f = px.scatter(pd.DataFrame(rr.values()), x="durasi_menit", y="susut_persen", hover_name="roast_id", title="Durasi roasting vs susut", color_discrete_sequence=[RED]); f.update_layout(**L); c2.plotly_chart(f)
    c3, c4 = st.columns(2)
    f = px.scatter(pd.DataFrame(hh.values()), x="lama_jemur_hari", y="kadar_air_kering_persen", hover_name="petani", title="Lama jemur vs kadar air", color_discrete_sequence=[LEAF]); f.update_layout(**L); c3.plotly_chart(f)
    f = px.bar(pd.DataFrame(DATA).sort_values("tgl_kemas"), x="fg_id", y="skor_intensitas", color="kategori_intensitas", title="Skor intensitas proses per batch",
               color_discrete_map={"Rendah": LEAF, "Sedang": CREMA, "Tinggi": RED}); f.update_layout(**L); c4.plotly_chart(f)
    st.markdown(f'<div class="note">{CATATAN}</div>', unsafe_allow_html=True)

with tab_a:
    st.subheader("Audit otomatis"); st.caption("Setiap batch diperiksa dengan 6 aturan. Arahkan kursor ke judul kolom untuk arti aturan.")
    aturan = [a["aturan"] for a in DATA[0]["audit"]]
    tabel = pd.DataFrame([{"Batch": d["fg_id"], "Status": d["status_audit"], **{f"R{j+1}": ("✓" if a["lulus"] else "✗") for j, a in enumerate(d["audit"])}} for d in DATA])
    st.dataframe(tabel, hide_index=True, column_config={f"R{j+1}": st.column_config.TextColumn(f"R{j+1}", help=t) for j, t in enumerate(aturan)})
    for j, t in enumerate(aturan): st.write(f"**R{j+1}.** {t}")
    st.markdown("##### Rincian temuan")
    tem = [{"Batch": d["fg_id"], "Aturan": a["aturan"], "Catatan": a["catatan"]} for d in DATA for a in d["audit"] if not a["lulus"]]
    st.dataframe(pd.DataFrame(tem), hide_index=True) if tem else st.success("Tidak ada temuan.")

with tab_p:
    st.subheader("Cara membaca dashboard ini")
    st.markdown("**Rantai 6 tahap:** panen, pascapanen (jemur natural), green bean, roasting, kemas, distribusi. Satu batch barang jadi berasal dari 1–3 batch roasting, satu lot green bean, dan 3 lot panen dari beberapa petani.")
    st.markdown("**Status audit:** *Lulus* = semua aturan terpenuhi. *Perlu ditinjau* = ada aturan tidak terpenuhi; temuan pada satu lot green bean menandai semua batch dari lot itu.")
    st.markdown("**Istilah:** Natural = ceri dijemur utuh. Hulling = pengupasan kulit kering. Rendemen = berat green bean dibanding ceri. Susut roasting = bobot hilang saat sangrai. Skor cupping 80+ = specialty.")
    st.markdown("**Batasan:** data simulasi; skor intensitas adalah asumsi tim, bukan emisi karbon; sistem ini menunjukkan ketertelusuran dan transparansi data, bukan jaminan anti-manipulasi.")
