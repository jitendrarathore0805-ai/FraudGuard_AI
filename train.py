from pathlib import Path
import json,joblib,numpy as np,pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder,StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import average_precision_score,roc_auc_score,precision_score,recall_score,f1_score,confusion_matrix
from xgboost import XGBClassifier
from data_loader import load_or_generate,FEATURES,CATEGORICAL,NUMERIC
ROOT=Path(__file__).resolve().parent; OUT=ROOT/"models"; OUT.mkdir(exist_ok=True)

def prep():
    return ColumnTransformer([("num",Pipeline([("imp",SimpleImputer(strategy="median")),("sc",StandardScaler())]),NUMERIC),("cat",Pipeline([("imp",SimpleImputer(strategy="most_frequent")),("oh",OneHotEncoder(handle_unknown="ignore"))]),CATEGORICAL)])
def threshold(y,p):
    ts=np.linspace(.05,.95,181); fs=[f1_score(y,p>=t,zero_division=0) for t in ts]; i=int(np.argmax(fs)); return float(ts[i]),float(fs[i])
def main():
    df=load_or_generate(); X=df[FEATURES]; y=df.fraud
    Xtr,Xtmp,ytr,ytmp=train_test_split(X,y,test_size=.30,stratify=y,random_state=42)
    Xv,Xte,yv,yte=train_test_split(Xtmp,ytmp,test_size=.50,stratify=ytmp,random_state=42)
    spw=(ytr==0).sum()/max((ytr==1).sum(),1)
    base={"Logistic Regression":LogisticRegression(max_iter=1500,class_weight="balanced",solver="liblinear",random_state=42),
          "Random Forest":RandomForestClassifier(n_estimators=180,max_depth=16,min_samples_leaf=2,class_weight="balanced_subsample",n_jobs=-1,random_state=42),
          "XGBoost":XGBClassifier(n_estimators=280,max_depth=5,learning_rate=.06,subsample=.85,colsample_bytree=.85,min_child_weight=2,reg_lambda=2,eval_metric="aucpr",scale_pos_weight=spw,tree_method="hist",n_jobs=-1,random_state=42)}
    results={}; pipes={}
    for name,est in base.items():
        pipe=Pipeline([("prep",prep()),("model",est)]); pipe.fit(Xtr,ytr); p=pipe.predict_proba(Xv)[:,1]; t,f=threshold(yv,p)
        results[name]={"validation_pr_auc":float(average_precision_score(yv,p)),"validation_f1":f,"threshold":t}; pipes[name]=pipe; print(name,results[name])
    best=max(results,key=lambda x:results[x]["validation_pr_auc"]); t=results[best]["threshold"]
    final=Pipeline([("prep",prep()),("model",base[best])]); final.fit(pd.concat([Xtr,Xv]),pd.concat([ytr,yv]))
    p=final.predict_proba(Xte)[:,1]; pred=p>=t
    tm={"pr_auc":float(average_precision_score(yte,p)),"roc_auc":float(roc_auc_score(yte,p)),"precision":float(precision_score(yte,pred,zero_division=0)),"recall":float(recall_score(yte,pred,zero_division=0)),"f1":float(f1_score(yte,pred,zero_division=0)),"confusion_matrix":confusion_matrix(yte,pred).tolist()}
    meta={"feature_columns":FEATURES,"best_model":best,"threshold":t,"dataset_rows":len(df),"fraud_transactions":int(y.sum()),"normal_transactions":int((y==0).sum()),"fraud_percentage":float(y.mean()*100),"models":results,"test_metrics":tm}
    joblib.dump(final,OUT/"best_model.pkl"); (OUT/"metadata.json").write_text(json.dumps(meta,indent=2))
    print("DONE |",best,"| threshold",t,"| test PR-AUC",tm["pr_auc"])
if __name__=="__main__": main()
