"""Membuat data SIMULASI satu produk: Kopi Arabika Gayo Natural, Medium Roast, kemasan 200 g.
Rantai: kebun -> lot panen -> lot green bean -> batch roasting -> batch barang jadi (finished good).
Semua nilai BUATAN (seed tetap). Ganti dengan data lapangan/CQI asli bila sudah ada; kolom dapat dipertahankan."""
import numpy as np, pandas as pd, json
from datetime import date, timedelta
rng = np.random.default_rng(7)
D = lambda x: x.isoformat()
# ---- 1. Kebun / petani ----
desa = [("Bener Meriah","Bener Kelipah"),("Aceh Tengah","Atu Lintang"),("Aceh Tengah","Pegasing"),("Aceh Tengah","Ketol"),
        ("Bener Meriah","Wih Pesam"),("Aceh Tengah","Bebesen"),("Aceh Tengah","Kebayakan"),("Bener Meriah","Permata")]
nama = ["Pak Ismail","Bu Salmah","Pak Rahmat","Pak Zulkifli","Bu Nurhayati","Pak Hasballah","Pak Anwar","Bu Fatimah","Pak Muksin","Pak Darwis","Bu Halimah","Pak Sulaiman"]
farms = [{"farm_id":f"KBN-{i+1:02d}","petani":nama[i],"kabupaten":desa[i%8][0],"desa":desa[i%8][1],
          "ketinggian_mdpl":int(rng.integers(1200,1620)),"luas_ha":round(float(rng.uniform(.8,3.2)),1),
          "varietas":str(rng.choice(["Gayo 1","Gayo 2","Ateng Super","Bourbon"],p=[.35,.3,.25,.1]))} for i in range(12)]
fdf = pd.DataFrame(farms)
# ---- 2. Lot panen (24) ----
harv=[]; start=date(2025,10,20)
for i in range(24):
    f=fdf.iloc[i%12]; t=start+timedelta(days=int(i*4+rng.integers(0,3)))
    kg=round(float(rng.uniform(220,620)),0); jemur=int(rng.integers(14,23)); sel=t+timedelta(days=1)
    harv.append({"harvest_id":f"PNN-{i+1:03d}","farm_id":f.farm_id,"tgl_panen":D(t),"berat_ceri_kg":kg,
      "ceri_merah_persen":round(float(rng.normal(93,3)),1),"ceri_apung_persen":round(float(abs(rng.normal(2.5,1))),1),
      "tgl_mulai_jemur":D(sel),"lama_jemur_hari":jemur,"tgl_selesai_jemur":D(sel+timedelta(days=jemur)),
      "metode_jemur":str(rng.choice(["Para-para (raised bed)","Terpal/lantai jemur"],p=[.6,.4])),
      "kadar_air_kering_persen":round(float(rng.normal(11.6,.5)),1)})
hdf=pd.DataFrame(harv)
# ---- 3. Lot green bean (8): tiap lot gabungan 3 lot panen berurutan ----
green=[]
for g in range(8):
    ids=hdf.iloc[g*3:g*3+3]; yld=float(rng.uniform(.185,.215))
    kg=round(float(ids.berat_ceri_kg.sum()*yld),1); hull=date.fromisoformat(ids.tgl_selesai_jemur.max())+timedelta(days=int(rng.integers(10,20)))
    green.append({"green_id":f"GRN-{g+1:02d}","harvest_ids":"|".join(ids.harvest_id),"tgl_hulling":D(hull),
      "berat_green_kg":kg,"rendemen_persen":round(kg/ids.berat_ceri_kg.sum()*100,1),
      "ukuran_ayakan":str(rng.choice(["Screen 17","Screen 18"],p=[.5,.5])),"cacat_per_300g":int(rng.integers(3,14)),
      "kadar_air_green_persen":round(float(rng.normal(11.4,.4)),1),"skor_cupping":round(float(rng.normal(84.2,1.1)),2),
      "gudang":"Gudang Green Bean Takengon","lama_simpan_hari":int(rng.integers(30,120))})
gdf=pd.DataFrame(green)
# ---- 4. Batch roasting & 5. batch barang jadi ----
roast=[]; fg=[]; rn=0; fn=0; cur_pool=[]
for _,g in gdf.iterrows():
    h=date.fromisoformat(g.tgl_hulling); r0=h+timedelta(days=int(g.lama_simpan_hari)); nr=int(rng.integers(3,6))
    used=0; rids=[]
    for j in range(nr):
        rn+=1; ch=round(float(rng.uniform(10,14)),1); used+=ch
        loss=float(rng.normal(14.5,1.2)); out=round(ch*(1-loss/100),2)
        roast.append({"roast_id":f"RST-{rn:03d}","green_id":g.green_id,"tgl_roasting":D(r0+timedelta(days=j//2)),
          "mesin":"Roaster drum 15 kg","level":"Medium","muatan_green_kg":ch,"suhu_charge_c":int(rng.integers(195,206)),
          "suhu_drop_c":int(rng.integers(208,218)),"durasi_menit":round(float(rng.normal(12.5,.8)),1),
          "susut_persen":round(loss,1),"berat_sangrai_kg":out}); rids.append(rn)
    # kelompokkan roast batch menjadi batch barang jadi (1-3 roast per FG)
    i=0
    while i<len(rids):
        k=int(rng.integers(1,min(3,len(rids)-i)+1)); grp=rids[i:i+k]; i+=k; fn+=1
        rr=[roast[x-1] for x in grp]; kgout=sum(x["berat_sangrai_kg"] for x in rr)
        bags=int(kgout*1000/200*rng.uniform(.96,.99)); pack=date.fromisoformat(rr[-1]["tgl_roasting"])+timedelta(days=int(rng.integers(2,6)))
        ship=pack+timedelta(days=int(rng.integers(3,10)))
        fg.append({"fg_id":f"FG-GYO-{pack:%y%m}-{fn:03d}","roast_ids":"|".join(f"RST-{x:03d}" for x in grp),"green_id":g.green_id,
          "produk":"Kopi Arabika Gayo Natural - Medium Roast - 200 g","tgl_kemas":D(pack),"jumlah_kemasan":bags,
          "tgl_kedaluwarsa":D(pack+timedelta(days=270)),"tujuan_distribusi":str(rng.choice(["Toko Kopi Bogor","Kafe Kampus IPB","Distributor Jakarta","Toko Daring"])),
          "tgl_kirim":D(ship)})
rdf=pd.DataFrame(roast); fgdf=pd.DataFrame(fg)
# ---- anomali sengaja (untuk menunjukkan fungsi audit) ----
gdf.loc[2,"kadar_air_green_persen"]=13.2                       # melebihi batas 12,5
rdf.loc[7,["susut_persen","berat_sangrai_kg"]]=[22.4,round(rdf.loc[7,"muatan_green_kg"]*(1-.224),2)]  # susut tak wajar
hdf.loc[5,"ceri_merah_persen"]=np.nan                           # data kosong
fgdf.loc[4,"jumlah_kemasan"]=int(fgdf.loc[4,"jumlah_kemasan"]*1.25)  # neraca massa tak seimbang
rdf.loc[20,"tgl_roasting"]=D(date.fromisoformat(gdf.set_index("green_id").loc[rdf.loc[20,"green_id"],"tgl_hulling"])-timedelta(days=3)) # urutan tanggal salah
# ---- skor intensitas proses (ASUMSI tim; bukan emisi) per batch barang jadi ----
def agg(r):
    rs=rdf[rdf.roast_id.isin(r.roast_ids.split("|"))]; hs=hdf[hdf.harvest_id.isin(gdf.set_index("green_id").loc[r.green_id,"harvest_ids"].split("|"))]
    return pd.Series({"lama_jemur":hs.lama_jemur_hari.mean(),"durasi":rs.durasi_menit.mean(),"susut":rs.susut_persen.mean()})
a=fgdf.apply(agg,axis=1); mm=lambda s:(s-s.min())/(s.max()-s.min()+1e-9)
fgdf["skor_intensitas"]=(100*(0.4*mm(a.lama_jemur)+0.3*mm(a.durasi)+0.3*mm(a.susut))).round(1)
fgdf["kategori_intensitas"]=pd.qcut(fgdf.skor_intensitas,3,labels=["Rendah","Sedang","Tinggi"]).astype(str)
for n,df in [("kebun",fdf),("lot_panen",hdf),("lot_green",gdf),("batch_roasting",rdf),("batch_barang_jadi",fgdf)]:
    df.to_csv(f"data/{n}.csv",index=False)
print({n:len(x) for n,x in [("kebun",fdf),("panen",hdf),("green",gdf),("roast",rdf),("fg",fgdf)]})
