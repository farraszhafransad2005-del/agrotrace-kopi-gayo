# AgroTrace Carbon Passport — Kopi Arabika Gayo Natural (Kelompok 8 ASDA 2026)
Produk tunggal: Kopi Arabika Gayo Natural, Medium Roast, kemasan 200 g.
Rantai: kebun/petani → lot panen → pascapanen (jemur natural) → lot green bean → batch roasting → batch barang jadi → distribusi.

## Mulai dari sini
Baca `Panduan_Menjalankan_AgroTrace.docx` (langkah rinci backend MongoDB + frontend Streamlit). Ringkas:
```
python -m venv venv && .\venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py                      # mode demo
python scripts/4_unggah_mongodb.py "<connection string>"   # lalu isi .streamlit/secrets.toml
```

## Dashboard satu berkas (demo cepat)
Klik dua kali `AgroTrace_Kopi_Dashboard.html` (Chrome/Edge). Tanpa instalasi, tanpa internet.

## Data
**Data SIMULASI** (seed tetap), bukan data lot nyata. Tabel di `data/`: kebun, lot_panen, lot_green, batch_roasting, batch_barang_jadi, serta `paspor.json` (gabungan + hasil audit).
Ganti dengan data lapangan: isi kelima CSV dengan kolom yang sama, lalu jalankan:
```
python scripts/2_buat_paspor.py
python scripts/3_buat_dashboard.py
```
(`1_buat_data.py` hanya pembuat data simulasi; jangan dijalankan bila memakai data asli.)

## MongoDB
`pip install pymongo pandas` lalu `python scripts/4_unggah_mongodb.py "<connection string>"` → database `agrotrace_kopi`.

## QR
Secara bawaan QR berisi `AGROTRACE|<kode batch>`. Setelah dashboard dihosting (mis. GitHub Pages), isi `BASE_URL` di `scripts/3_buat_dashboard.py` agar QR membuka halaman batch langsung (`...html#FG-GYO-xxxx`).

## Batasan
Skor intensitas = proxy proses (lama jemur 40%, durasi roasting 30%, susut 30%), asumsi tim, bukan emisi karbon. Ketertelusuran = transparansi data, bukan jaminan anti-manipulasi.
