"""Unggah ke MongoDB: 5 tabel + koleksi 'paspor' (dokumen gabungan per batch barang jadi).
Pakai: python scripts/4_unggah_mongodb.py "mongodb+srv://USER:PASS@cluster0.xxxx.mongodb.net/"  (butuh: pip install pymongo pandas)"""
import sys, json, pandas as pd
from pymongo import MongoClient
db = MongoClient(sys.argv[1], serverSelectionTimeoutMS=8000)["agrotrace_kopi"]
for n in ["kebun","lot_panen","lot_green","batch_roasting","batch_barang_jadi"]:
    df = pd.read_csv(f"data/{n}.csv").astype(object).where(lambda x: x.notna(), None)
    db[n].delete_many({}); db[n].insert_many(df.to_dict("records")); print(n, db[n].count_documents({}))
p = json.load(open("data/paspor.json"))
db["paspor"].delete_many({}); db["paspor"].insert_many(p); db["paspor"].create_index("fg_id", unique=True)
print("paspor", db["paspor"].count_documents({}))
