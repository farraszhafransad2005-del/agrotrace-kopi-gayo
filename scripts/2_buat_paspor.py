"""Gabungkan 5 tabel menjadi dokumen 'paspor' per batch barang jadi + hasil audit otomatis.
Keluaran: data/paspor.json (siap diunggah ke MongoDB, koleksi 'paspor')."""
import pandas as pd, json, math
from datetime import date
L=lambda n: pd.read_csv(f"data/{n}.csv")
F,H,G,R,P=[L(x) for x in ["kebun","lot_panen","lot_green","batch_roasting","batch_barang_jadi"]]
clean=lambda d:{k:(None if (isinstance(v,float) and math.isnan(v)) else (v.item() if hasattr(v,"item") else v)) for k,v in d.items()}
dt=date.fromisoformat
out=[]
for _,p in P.iterrows():
    g=G[G.green_id==p.green_id].iloc[0]; rs=R[R.roast_id.isin(p.roast_ids.split("|"))]
    hs=H[H.harvest_id.isin(g.harvest_ids.split("|"))].merge(F,on="farm_id")
    ch=[]
    def chk(rule,ok,msg): ch.append({"aturan":rule,"lulus":bool(ok),"catatan":msg})
    # R1 kadar air green
    chk("Kadar air green bean <= 12,5%",g.kadar_air_green_persen<=12.5,f"{g.green_id}: {g.kadar_air_green_persen}%")
    # R2 susut roasting
    bad=rs[(rs.susut_persen<10)|(rs.susut_persen>20)]
    chk("Susut roasting 10-20%",bad.empty,"semua batch wajar" if bad.empty else "; ".join(f"{r.roast_id}: {r.susut_persen}%" for r in bad.itertuples()))
    # R3 neraca massa
    kg=rs.berat_sangrai_kg.sum(); pack=p.jumlah_kemasan*0.2
    chk("Neraca massa: berat kemasan <= berat sangrai",pack<=kg+1e-6,f"kemasan {pack:.1f} kg vs sangrai {kg:.1f} kg")
    # R4 kelengkapan
    miss=[c for c in ["ceri_merah_persen","ceri_apung_persen","kadar_air_kering_persen","lama_jemur_hari"] if hs[c].isna().any()]
    chk("Data lot panen lengkap",not miss,"lengkap" if not miss else "kosong: "+", ".join(miss))
    # R5 urutan tanggal
    ok=all(dt(a)<=dt(b) for a,b in [(hs.tgl_selesai_jemur.max(),g.tgl_hulling),(g.tgl_hulling,rs.tgl_roasting.min()),(rs.tgl_roasting.max(),p.tgl_kemas),(p.tgl_kemas,p.tgl_kirim),(p.tgl_kemas,p.tgl_kedaluwarsa)])
    chk("Urutan tanggal logis (panen > jemur > hulling > roasting > kemas > kirim)",ok,"berurutan" if ok else "ada tanggal yang mendahului tahap sebelumnya")
    # R6 rendemen
    chk("Rendemen ceri ke green bean 15-25%",15<=g.rendemen_persen<=25,f"{g.rendemen_persen}%")
    out.append(clean({**p.to_dict(),
      "panen":[clean(r) for r in hs.to_dict("records")],"green":clean(g.to_dict()),"roasting":[clean(r) for r in rs.to_dict("records")],
      "audit":ch,"status_audit":"Lulus" if all(c["lulus"] for c in ch) else "Perlu ditinjau"}))
json.dump(out,open("data/paspor.json","w"),ensure_ascii=False,indent=1)
print(len(out),"paspor;",sum(o["status_audit"]!="Lulus" for o in out),"perlu ditinjau")
