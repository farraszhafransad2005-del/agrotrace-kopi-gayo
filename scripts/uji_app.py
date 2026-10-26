import sys, json, mongomock, pymongo, os
from streamlit.testing.v1 import AppTest
at = AppTest.from_file("../app.py", default_timeout=60).run(); print("demo:", at.exception, [m.value for m in at.metric][:2], at.caption[0].value[:40])
for i in range(6):
    at.radio[0].set_value(["Panen","Pascapanen","Green bean","Roasting","Kemas","Distribusi"][i]).run(); assert not at.exception, at.exception
at.selectbox[0].set_value("FG-GYO-2604-003").run(); print("batch 003:", [e.value[:30] for e in at.markdown if "badge" in e.value][:1], at.exception)
fake = mongomock.MongoClient(); fake["agrotrace_kopi"]["paspor"].insert_many(json.load(open("data/paspor.json")))
pymongo.MongoClient = lambda *a, **k: fake; os.environ["MONGO_URI"] = "mongodb://x"
import streamlit as st; st.cache_data.clear()
at = AppTest.from_file("../app.py", default_timeout=60).run(); print("mongo:", at.exception, at.caption[0].value[:30])
import streamlit as st; st.cache_data.clear(); pymongo.MongoClient = lambda *a, **k: (_ for _ in ()).throw(ConnectionError("x"))
at = AppTest.from_file("../app.py", default_timeout=60).run(); print("putus:", [e.value[:35] for e in at.error])
