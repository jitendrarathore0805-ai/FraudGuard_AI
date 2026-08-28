from pathlib import Path
import numpy as np, pandas as pd
ROOT=Path(__file__).resolve().parent
CSV_PATH=ROOT/"data"/"human_transactions.csv"
FEATURES=["amount","hour","merchant_category","transaction_type","location_risk","device_trust","international","card_present","distance_km","velocity_1h","avg_amount_30d","account_age_days","failed_attempts_24h","previous_fraud_count"]
CATEGORICAL=["merchant_category","transaction_type"]
NUMERIC=[x for x in FEATURES if x not in CATEGORICAL]

def generate_dataset(n=80000,seed=42):
    r=np.random.default_rng(seed)
    merchant=r.choice(["Grocery","Fuel","Dining","Shopping","Electronics","Travel","Gaming","Cash"],n,p=[.20,.12,.14,.20,.10,.08,.07,.09])
    tx=r.choice(["POS","Online","Contactless","ATM","Mobile"],n,p=[.28,.35,.18,.07,.12])
    amount=np.clip(r.lognormal(5,1,n),5,50000); hour=r.integers(0,24,n)
    loc=np.clip(r.beta(2,7,n),0,1); device=np.clip(r.beta(7,2,n),0,1)
    intl=r.binomial(1,.12,n); card=r.binomial(1,.55,n)
    dist=np.clip(r.exponential(12,n),0,1500); velocity=np.clip(r.poisson(1.3,n),0,20)
    avg=np.clip(r.lognormal(4.8,.75,n),10,25000); age=r.integers(5,5000,n)
    failed=np.clip(r.poisson(.25,n),0,8); prev=np.clip(r.poisson(.04,n),0,5)
    late=((hour<=4)|(hour>=23)).astype(float); unusual=np.clip(np.log1p(amount)-np.log1p(avg),-1,4)
    score=(-5.5+1.25*late+1.45*intl+2.1*(1-device)+1.6*loc+.9*np.clip(velocity/8,0,1)+.7*unusual+.9*(tx=="Online")+.65*np.isin(merchant,["Electronics","Gaming","Cash"])+.8*(1-card)+.7*(age<30)+.7*failed+.9*prev+.25*np.log1p(dist)+r.normal(0,.75,n))
    p=1/(1+np.exp(-score)); fraud=r.binomial(1,np.clip(p,0,.98))
    return pd.DataFrame({"amount":amount,"hour":hour,"merchant_category":merchant,"transaction_type":tx,"location_risk":loc,"device_trust":device,"international":intl,"card_present":card,"distance_km":dist,"velocity_1h":velocity,"avg_amount_30d":avg,"account_age_days":age,"failed_attempts_24h":failed,"previous_fraud_count":prev,"fraud":fraud})

def load_or_generate():
    CSV_PATH.parent.mkdir(exist_ok=True)
    if CSV_PATH.exists(): return pd.read_csv(CSV_PATH)
    df=generate_dataset(); df.to_csv(CSV_PATH,index=False); return df
