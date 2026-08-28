from pathlib import Path
import json,joblib,pandas as pd,streamlit as st,plotly.express as px,plotly.graph_objects as go
from database import init_db,register,login,add,history,stats,update
ROOT=Path(__file__).resolve().parent; M=ROOT/"models"; init_db()
st.set_page_config(page_title="FraudGuard AI",page_icon="🛡️",layout="wide")
st.markdown("""<style>
.stApp{background:#F6F8FC} [data-testid=stSidebar]{background:#fff;border-right:1px solid #E7ECF3}
.brand{display:flex;gap:12px;align-items:center;padding:8px 3px 22px}.logo{width:44px;height:44px;border-radius:13px;background:#2563EB;color:#fff;display:flex;align-items:center;justify-content:center;font-size:23px}
.title{font-size:30px;font-weight:800;color:#0F172A}.sub{color:#64748B;margin-bottom:20px}.card,.kpi{background:#fff;border:1px solid #E7ECF3;border-radius:16px;padding:19px;box-shadow:0 5px 18px rgba(15,23,42,.04)}.klabel{color:#64748B;font-size:12px}.kvalue{font-size:25px;font-weight:800;margin-top:4px}.high{background:#FFF1F2;color:#DC2626;border:1px solid #FECDD3;border-radius:12px;padding:12px;text-align:center;font-weight:800}.low{background:#ECFDF5;color:#059669;border:1px solid #A7F3D0;border-radius:12px;padding:12px;text-align:center;font-weight:800}
</style>""",unsafe_allow_html=True)

if not (M/"best_model.pkl").exists():
 st.error("Model missing. Run: python train.py"); st.stop()
model=joblib.load(M/"best_model.pkl"); meta=json.loads((M/"metadata.json").read_text())

if "user" not in st.session_state: st.session_state.user=None
if not st.session_state.user:
 st.markdown("<div style='text-align:center;margin:55px 0 20px'><div style='font-size:48px'>🛡️</div><div style='font-size:32px;font-weight:800;color:#172554'>FraudGuard AI</div><div style='color:#64748B'>Secure Transaction Intelligence</div></div>",unsafe_allow_html=True)
 a,b=st.tabs(["Sign in","Create account"])
 with a:
  with st.form("login"):
   u=st.text_input("Username or email"); p=st.text_input("Password",type="password"); ok=st.form_submit_button("Sign in",type="primary",use_container_width=True)
  if ok:
   x=login(u,p)
   if x: st.session_state.user=x; st.rerun()
   else: st.error("Invalid credentials.")
 with b:
  with st.form("signup"):
   n=st.text_input("Full name"); u=st.text_input("Username"); e=st.text_input("Email"); p=st.text_input("Password",type="password"); q=st.text_input("Confirm password",type="password"); ok=st.form_submit_button("Create account",use_container_width=True)
  if ok:
   if len(p)<6: st.error("Password must be at least 6 characters.")
   elif p!=q: st.error("Passwords do not match.")
   elif register(u,e,p,n): st.success("Account created. Sign in now.")
   else: st.error("Username/email already exists.")
 st.stop()

user=st.session_state.user
with st.sidebar:
 st.markdown(f"<div class='brand'><div class='logo'>🛡</div><div><b style='font-size:20px;color:#172554'>FRAUDGUARD AI</b><div style='color:#64748B;font-size:11px'>Transaction Intelligence</div></div></div>",unsafe_allow_html=True)
 st.info(f"👋 {user['full_name'] or user['username']}\n\n{user['email']}")
 page=st.radio("Navigation",["Dashboard","Analyze Transaction","Transaction History","My Profile","Analytics","Model Performance","About"],label_visibility="collapsed")
 if st.button("Log out",use_container_width=True): st.session_state.user=None; st.rerun()

st.markdown("<div class='title'>Credit Card Fraud Intelligence</div><div class='sub'>Smart transaction monitoring with explainable machine learning</div>",unsafe_allow_html=True)
s=stats(user["id"]); hist=history(user["id"])
if page=="Dashboard":
 c1,c2,c3,c4=st.columns(4)
 for c,label,val in zip([c1,c2,c3,c4],["My Transactions","Fraud Alerts","Average Risk","Model"],[f"{s['total']:,}",f"{s['fraud']:,}",f"{s['risk']*100:.1f}%",meta["best_model"]]):
  c.markdown(f"<div class='kpi'><div class='klabel'>{label}</div><div class='kvalue'>{val}</div></div>",unsafe_allow_html=True)
 st.write("")
 st.markdown("<div class='card'><b>Quick Transaction Check</b><br><span style='color:#64748B;font-size:12px'>No V1–V28 fields. Only meaningful information.</span></div>",unsafe_allow_html=True)
 with st.form("quick"):
  a,b,c,d=st.columns(4)
  amount=a.number_input("Amount (₹)",1.0,500000.0,2500.0); avg=b.number_input("30-day average (₹)",1.0,500000.0,1500.0)
  merchant=c.selectbox("Merchant",["Grocery","Fuel","Dining","Shopping","Electronics","Travel","Gaming","Cash"]); tx=d.selectbox("Type",["POS","Online","Contactless","ATM","Mobile"])
  a,b,c,d=st.columns(4); hour=a.slider("Hour",0,23,14); intl=b.selectbox("International",["No","Yes"]); card=c.selectbox("Card present",["Yes","No"]); velocity=d.number_input("Transactions last hour",0,50,1)
  ok=st.form_submit_button("🔎 Analyze Transaction",type="primary",use_container_width=True)
 if ok:
  data=dict(amount=amount,hour=hour,merchant_category=merchant,transaction_type=tx,location_risk=.25,device_trust=.8,international=int(intl=="Yes"),card_present=int(card=="Yes"),distance_km=5.,velocity_1h=velocity,avg_amount_30d=avg,account_age_days=800,failed_attempts_24h=0,previous_fraud_count=0)
  p=float(model.predict_proba(pd.DataFrame([data]))[0,1]); pred=int(p>=meta["threshold"]); add(user["id"],data,p,pred); st.session_state.result=(p,pred); st.success("Analyzed and saved to your history.")
 if "result" in st.session_state:
  p,pred=st.session_state.result; a,b=st.columns(2)
  with a: st.metric("Fraud Probability",f"{p*100:.2f}%")
  with b: st.markdown("<div class='high'>⚠ HIGH RISK — FRAUD</div>" if pred else "<div class='low'>✓ LOW RISK — NORMAL</div>",unsafe_allow_html=True)

elif page=="Analyze Transaction":
 st.markdown("### Analyze Transaction")
 with st.form("full"):
  a,b,c,d=st.columns(4)
  amount=a.number_input("Amount (₹)",1.,500000.,2500.); avg=a.number_input("Your 30-day average (₹)",1.,500000.,1500.)
  merchant=b.selectbox("Merchant category",["Grocery","Fuel","Dining","Shopping","Electronics","Travel","Gaming","Cash"]); tx=b.selectbox("Transaction type",["POS","Online","Contactless","ATM","Mobile"])
  hour=c.slider("Hour",0,23,14); location=c.slider("Location risk",0.,1.,.2); device=c.slider("Device trust",0.,1.,.85)
  intl=d.selectbox("International",["No","Yes"]); card=d.selectbox("Card present",["Yes","No"]); distance=d.number_input("Distance from usual location (km)",0.,5000.,5.); velocity=d.number_input("Transactions last hour",0,50,1)
  age=a.number_input("Account age (days)",1,10000,800); failed=b.number_input("Failed attempts in 24h",0,30,0); prev=c.number_input("Previous fraud alerts",0,50,0)
  ok=st.form_submit_button("🛡️ Check Fraud Risk",type="primary",use_container_width=True)
 if ok:
  data=dict(amount=amount,hour=hour,merchant_category=merchant,transaction_type=tx,location_risk=location,device_trust=device,international=int(intl=="Yes"),card_present=int(card=="Yes"),distance_km=distance,velocity_1h=velocity,avg_amount_30d=avg,account_age_days=age,failed_attempts_24h=failed,previous_fraud_count=prev)
  p=float(model.predict_proba(pd.DataFrame([data]))[0,1]); pred=int(p>=meta["threshold"]); add(user["id"],data,p,pred)
  st.metric("Fraud Probability",f"{p*100:.2f}%"); st.markdown("<div class='high'>⚠ HIGH RISK — FRAUD</div>" if pred else "<div class='low'>✓ LOW RISK — NORMAL</div>",unsafe_allow_html=True)

elif page=="Transaction History":
 st.markdown("### My Transaction History")
 if hist:
  h=pd.DataFrame(hist); h["Status"]=h.prediction.map({0:"✓ Normal",1:"⚠ Fraud"}); h["Risk"]=h.probability.map(lambda x:f"{x*100:.2f}%")
  st.dataframe(h[["id","created_at","amount","merchant_category","transaction_type","Risk","Status"]],use_container_width=True,hide_index=True)
  st.download_button("Download my history CSV",h.to_csv(index=False),"my_transactions.csv")
 else: st.info("No transactions yet.")

elif page=="My Profile":
 st.markdown("### My Profile")
 with st.form("profile"):
  n=st.text_input("Full name",user["full_name"] or ""); e=st.text_input("Email",user["email"]); st.text_input("Username",user["username"],disabled=True); ok=st.form_submit_button("Save profile",type="primary")
 if ok and update(user["id"],n,e): st.session_state.user["full_name"]=n; st.session_state.user["email"]=e; st.success("Profile updated.")

elif page=="Analytics":
 st.markdown("### Personal Analytics")
 if hist:
  h=pd.DataFrame(hist); a,b=st.columns(2)
  with a: st.plotly_chart(px.histogram(h,x="probability",nbins=20,title="My Risk Distribution"),use_container_width=True)
  with b: st.plotly_chart(px.bar(h.groupby("merchant_category",as_index=False).probability.mean(),x="merchant_category",y="probability",title="Average Risk by Merchant"),use_container_width=True)
 else: st.info("Analyze transactions to populate analytics.")

elif page=="Model Performance":
 st.markdown("### Model Performance")
 rows=[{"Model":n,**r} for n,r in meta["models"].items()]; st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
 tm=meta["test_metrics"]; a,b,c,d,e=st.columns(5)
 for col,label,val in zip([a,b,c,d,e],["PR-AUC","ROC-AUC","Precision","Recall","F1"],[tm["pr_auc"],tm["roc_auc"],tm["precision"],tm["recall"],tm["f1"]]): col.metric(label,f"{val:.4f}")
 st.caption(f"Best model: {meta['best_model']} | threshold: {meta['threshold']:.3f}")

else:
 st.markdown("### About FraudGuard AI")
 st.markdown(f"<div class='card'><b>Human-readable fraud detection</b><br><br>This version intentionally does not ask users for V1–V28. Those are anonymized dataset features. The project uses a synthetic, human-readable transaction dataset for a coherent demo workflow.<br><br><b>ML:</b> Logistic Regression + Random Forest + XGBoost<br><b>Database:</b> SQLite<br><b>Authentication:</b> bcrypt-hashed local accounts<br><b>Best model:</b> {meta['best_model']}</div>",unsafe_allow_html=True)
