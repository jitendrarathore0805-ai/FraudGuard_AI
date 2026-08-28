import sqlite3,bcrypt
from pathlib import Path
from datetime import datetime
DB=Path(__file__).resolve().parent/"fraudguard.db"
def con(): c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c
def init_db():
 c=con(); c.execute("CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,username TEXT UNIQUE,email TEXT UNIQUE,password_hash BLOB,full_name TEXT,created_at TEXT)"); c.execute("CREATE TABLE IF NOT EXISTS transactions(id INTEGER PRIMARY KEY,user_id INTEGER,created_at TEXT,amount REAL,merchant_category TEXT,transaction_type TEXT,location_risk REAL,device_trust REAL,international INTEGER,card_present INTEGER,distance_km REAL,velocity_1h INTEGER,avg_amount_30d REAL,account_age_days INTEGER,failed_attempts_24h INTEGER,previous_fraud_count INTEGER,probability REAL,prediction INTEGER)"); c.commit(); c.close()
def register(u,e,p,n):
 try:
  c=con(); c.execute("INSERT INTO users(username,email,password_hash,full_name,created_at) VALUES(?,?,?,?,?)",(u,e.lower(),bcrypt.hashpw(p.encode(),bcrypt.gensalt()),n,datetime.now().isoformat(timespec="seconds"))); c.commit(); c.close(); return True
 except sqlite3.IntegrityError: return False
def login(u,p):
 c=con(); r=c.execute("SELECT * FROM users WHERE username=? OR email=?",(u,u.lower())).fetchone(); c.close()
 return dict(r) if r and bcrypt.checkpw(p.encode(),r["password_hash"]) else None
def add(uid,d,predprob,pred):
 c=con(); c.execute("INSERT INTO transactions VALUES(NULL,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(uid,datetime.now().isoformat(timespec="seconds"),d["amount"],d["merchant_category"],d["transaction_type"],d["location_risk"],d["device_trust"],d["international"],d["card_present"],d["distance_km"],d["velocity_1h"],d["avg_amount_30d"],d["account_age_days"],d["failed_attempts_24h"],d["previous_fraud_count"],predprob,pred)); c.commit(); c.close()
def history(uid):
 c=con(); r=c.execute("SELECT * FROM transactions WHERE user_id=? ORDER BY id DESC",(uid,)).fetchall(); c.close(); return [dict(x) for x in r]
def stats(uid):
 c=con(); r=c.execute("SELECT COUNT(*) total,COALESCE(SUM(prediction),0) fraud,COALESCE(AVG(probability),0) risk FROM transactions WHERE user_id=?",(uid,)).fetchone(); c.close(); return dict(r)
def update(uid,name,email):
 try:
  c=con(); c.execute("UPDATE users SET full_name=?,email=? WHERE id=?",(name,email.lower(),uid)); c.commit(); c.close(); return True
 except sqlite3.IntegrityError: return False
