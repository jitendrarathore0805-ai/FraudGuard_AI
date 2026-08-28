# FraudGuard AI v2
Light/white Streamlit fraud dashboard with meaningful transaction inputs, per-user local accounts, profiles, SQLite history, model comparison and threshold selection.

## Run
cd /d C:\Users\HP\Downloads\FraudGuard_AI_v2
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python train.py
streamlit run app.py

## Login
Local username/email + bcrypt password accounts are included. Each user's transaction history is separated by user_id.

## Google Login
Google OAuth requires your own Google Cloud OAuth client. Streamlit's OIDC (`st.login`/`st.user`) can be added once client credentials and a deployed callback URL are configured. This ZIP deliberately does not contain fake credentials.

## ML note
V1-V28 from the ULB/Kaggle dataset are anonymized. Instead of pretending those values are user inputs, this portfolio build generates a human-readable synthetic transaction dataset with amount, merchant, type, risk, device trust, international flag, card presence, velocity, account age and history features.
