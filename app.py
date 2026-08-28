from pathlib import Path
import json

import joblib
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from database import (
    init_db,
    register,
    login,
    google_login_or_register,
    add,
    history,
    stats,
    update,
)


# ============================================================
# PAGE CONFIG
# IMPORTANT: This must come before other Streamlit commands
# ============================================================

st.set_page_config(
    page_title="FraudGuard AI",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

ROOT = Path(__file__).resolve().parent
MODEL_DIR = ROOT / "models"

MODEL_PATH = MODEL_DIR / "best_model.pkl"
META_PATH = MODEL_DIR / "metadata.json"

try:
    init_db()
except Exception as e:
    st.error("Database initialization failed.")
    st.exception(e)
    st.stop()


st.markdown(
    """
    <style>

 
    @import url(
        'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap'
    );

    html,
    body,
    [class*="css"] {
        font-family: "Inter", sans-serif;
    }

    .stApp {
        background:
            radial-gradient(
                circle at 10% 0%,
                rgba(37, 99, 235, 0.07),
                transparent 30%
            ),
            #F7F9FC;
    }


    section[data-testid="stSidebar"] {
        background: #FFFFFF;
        border-right: 1px solid #E6EBF2;
    }

    section[data-testid="stSidebar"] > div {
        padding-top: 1.2rem;
    }

    .stButton > button,
    .stFormSubmitButton > button {
        border-radius: 10px;
        min-height: 42px;
        font-weight: 600;
        border: 1px solid #D9E1EC;
        transition: all 0.2s ease;
    }

    .stButton > button:hover,
    .stFormSubmitButton > button:hover {
        transform: translateY(-1px);
    }


    .stTextInput input,
    .stNumberInput input,
    .stSelectbox div[data-baseweb="select"],
    .stDateInput input {
        border-radius: 10px;
    }


    .login-space {
        height: 45px;
    }

    .login-icon {
        font-size: 58px;
        text-align: center;
        margin-bottom: 5px;
    }

    .login-heading {
        text-align: center;
        font-size: 34px;
        font-weight: 800;
        color: #172554;
        margin-bottom: 3px;
    }

    .login-subheading {
        text-align: center;
        color: #64748B;
        font-size: 14px;
        margin-bottom: 25px;
    }


    .brand-title {
        font-size: 21px;
        font-weight: 800;
        color: #172554;
    }

    .brand-subtitle {
        color: #64748B;
        font-size: 11px;
    }


    .page-heading {
        font-size: 31px;
        font-weight: 800;
        color: #0F172A;
        letter-spacing: -0.03em;
    }

    .page-description {
        color: #64748B;
        margin-top: -8px;
        margin-bottom: 24px;
    }


    .muted {
        color: #64748B;
        font-size: 13px;
    }


    .high-risk {
        padding: 20px;
        border-radius: 15px;
        background: #FFF1F2;
        border: 1px solid #FECDD3;
        text-align: center;
    }

    .medium-risk {
        padding: 20px;
        border-radius: 15px;
        background: #FFFBEB;
        border: 1px solid #FDE68A;
        text-align: center;
    }

    .low-risk {
        padding: 20px;
        border-radius: 15px;
        background: #ECFDF5;
        border: 1px solid #A7F3D0;
        text-align: center;
    }

    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }

    header {
        background: transparent !important;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


if not MODEL_PATH.exists():
    st.error(
        f"Model file not found:\n\n{MODEL_PATH}"
    )
    st.info(
        "Please make sure best_model.pkl exists inside the models folder."
    )
    st.stop()


if not META_PATH.exists():
    st.error(
        f"Metadata file not found:\n\n{META_PATH}"
    )
    st.info(
        "Please make sure metadata.json exists inside the models folder."
    )
    st.stop()


try:

    model = joblib.load(MODEL_PATH)

    with open(
        META_PATH,
        "r",
        encoding="utf-8"
    ) as f:
        meta = json.load(f)

except Exception as e:

    st.error("Unable to load the fraud detection model.")
    st.exception(e)
    st.stop()

if "user" not in st.session_state:
    st.session_state.user = None

if "result" not in st.session_state:
    st.session_state.result = None


def google_user_available():

    try:
        return bool(st.user.is_logged_in)

    except Exception:
        return False


def sync_google_user():

    if not google_user_available():
        return None

    try:

        google_data = st.user.to_dict()

        email = google_data.get(
            "email",
            ""
        )

        name = google_data.get(
            "name",
            ""
        )

        picture = google_data.get(
            "picture",
            ""
        )

        google_sub = google_data.get(
            "sub",
            ""
        )

        if not email or not google_sub:
            return None

        user = google_login_or_register(
            google_sub=google_sub,
            email=email,
            name=name,
            picture=picture,
        )

        return user

    except Exception as e:

        st.error(
            "Google authentication succeeded, "
            "but the user could not be synchronized."
        )

        st.exception(e)

        return None


def show_auth_screen():

    st.markdown(
        '<div class="login-space"></div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="login-icon">🛡️</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="login-heading">FraudGuard AI</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="login-subheading">'
        'Secure Transaction Intelligence'
        '</div>',
        unsafe_allow_html=True
    )

    left, center, right = st.columns(
        [1, 2, 1]
    )

    with center:

        with st.container(border=True):

            st.subheader("Welcome back")

            st.caption(
                "Sign in to monitor and analyze transactions."
            )

            st.write("")

            if st.button(
                " 🌐 Continue with Google",
                use_container_width=True,
                key="google_login_button"
            ):

                try:

                    st.login()

                except Exception as e:

                    st.error(
                        "Google Sign-In could not be started."
                    )

                    st.exception(e)

            st.write("")

            st.divider()

            st.caption(
                "Or continue with your FraudGuard account"
            )

            login_tab, signup_tab = st.tabs(
                [
                    "Sign in",
                    "Create account"
                ]
            )

            with login_tab:

                with st.form(
                    "local_login_form"
                ):

                    identifier = st.text_input(
                        "Username or email",
                        placeholder="you@example.com",
                    )

                    password = st.text_input(
                        "Password",
                        type="password",
                        placeholder="Enter your password",
                    )

                    submitted = st.form_submit_button(
                        "Sign in",
                        type="primary",
                        use_container_width=True,
                    )

                if submitted:

                    if not identifier.strip():

                        st.warning(
                            "Please enter your username or email."
                        )

                    elif not password:

                        st.warning(
                            "Please enter your password."
                        )

                    else:

                        try:

                            user = login(
                                identifier.strip(),
                                password
                            )

                            if user:

                                st.session_state.user = user
                                st.session_state.result = None

                                st.rerun()

                            else:

                                st.error(
                                    "Invalid username/email or password."
                                )

                        except Exception as e:

                            st.error(
                                "Login failed."
                            )

                            st.exception(e)

           
            with signup_tab:

                with st.form(
                    "signup_form"
                ):

                    full_name = st.text_input(
                        "Full name",
                        placeholder="Jitendra Rathore",
                    )

                    username = st.text_input(
                        "Username",
                        placeholder="jitendra123",
                    )

                    email = st.text_input(
                        "Email",
                        placeholder="you@example.com",
                    )

                    password = st.text_input(
                        "Password",
                        type="password",
                    )

                    confirm_password = st.text_input(
                        "Confirm password",
                        type="password",
                    )

                    submitted = st.form_submit_button(
                        "Create account",
                        use_container_width=True,
                    )

                if submitted:

                    full_name = full_name.strip()
                    username = username.strip()
                    email = email.strip()

                    if not full_name:

                        st.warning(
                            "Please enter your full name."
                        )

                    elif not username:

                        st.warning(
                            "Please enter a username."
                        )

                    elif not email:

                        st.warning(
                            "Please enter your email."
                        )

                    elif len(password) < 6:

                        st.warning(
                            "Password must contain at least 6 characters."
                        )

                    elif password != confirm_password:

                        st.error(
                            "Passwords do not match."
                        )

                    else:

                        try:

                            created = register(
                                username,
                                email,
                                password,
                                full_name,
                            )

                            if created:

                                st.success(
                                    "Account created successfully!"
                                )

                                st.info(
                                    "Open the Sign in tab and "
                                    "login with your account."
                                )

                            else:

                                st.error(
                                    "Username or email already exists."
                                )

                        except Exception as e:

                            st.error(
                                "Account creation failed."
                            )

                            st.exception(e)

            st.write("")

            st.caption(
                " Your transaction data is isolated to your account."
            )


if st.session_state.user is None:

    google_user = sync_google_user()

    if google_user:

        st.session_state.user = google_user
        st.session_state.result = None

        st.rerun()

    show_auth_screen()

    st.stop()


user = st.session_state.user


with st.sidebar:

    st.markdown(
        "## 🛡️ FraudGuard AI"
    )

    st.caption(
        "Transaction Intelligence"
    )

    st.divider()

    user_name = (
        user.get("full_name")
        or user.get("username")
        or "User"
    )

    user_email = user.get(
        "email",
        ""
    )

    st.write(
        f"👤 **{user_name}**"
    )

    if user_email:

        st.caption(
            user_email
        )

    st.divider()

    page = st.radio(
        "Navigation",
        [
            "Dashboard",
            "Analyze Transaction",
            "Transaction History",
            "My Profile",
            "Analytics",
            "Model Performance",
            "About",
        ],
        label_visibility="collapsed",
    )

    st.divider()

    auth_provider = user.get(
        "auth_provider",
        "local"
    )

    if auth_provider == "google":

        if st.button(
            "↪ Sign out",
            use_container_width=True,
            key="google_logout"
        ):

            st.session_state.user = None
            st.session_state.result = None

            try:
                st.logout()
            except Exception:
                st.rerun()

    else:

        if st.button(
            "↪ Log out",
            use_container_width=True,
            key="local_logout"
        ):

            st.session_state.user = None
            st.session_state.result = None

            st.rerun()

try:

    stats_data = stats(
        user["id"]
    )

except Exception:

    stats_data = {
        "total": 0,
        "fraud": 0,
        "risk": 0,
    }


try:

    hist = history(
        user["id"]
    )

except Exception:

    hist = []



st.markdown(
    '<div class="page-heading">'
    'Credit Card Fraud Intelligence'
    '</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="page-description">'
    'Smart transaction monitoring powered by explainable machine learning'
    '</div>',
    unsafe_allow_html=True
)

def predict_transaction(data):

    try:

        dataframe = pd.DataFrame(
            [data]
        )

        probability = float(
            model.predict_proba(
                dataframe
            )[0, 1]
        )

        threshold = float(
            meta.get(
                "threshold",
                0.5
            )
        )

        prediction = int(
            probability >= threshold
        )

        return probability, prediction

    except Exception as e:

        st.error(
            "Model prediction failed."
        )

        st.exception(e)

        return None, None


def show_result(
    probability,
    prediction
):

    if probability is None:
        return

    st.write("")

    result_left, result_right = st.columns(
        2
    )

    with result_left:

        with st.container(border=True):

            st.subheader(
                "Fraud Probability"
            )

            st.metric(
                "Risk Score",
                f"{probability * 100:.2f}%"
            )

            st.progress(
                min(
                    max(
                        probability,
                        0.0
                    ),
                    1.0
                )
            )

            threshold = float(
                meta.get(
                    "threshold",
                    0.5
                )
            )

            st.caption(
                f"Decision threshold: {threshold:.3f}"
            )

    with result_right:

        if prediction == 1:

            st.error(
                " HIGH RISK"
            )

            st.write(
                "This transaction has been flagged "
                "as potentially fraudulent."
            )

        else:

            st.success(
                "✓ LOW RISK"
            )

            st.write(
                "This transaction appears to be normal."
            )


if page == "Dashboard":

    st.subheader(
        "Overview"
    )

    c1, c2, c3, c4 = st.columns(
        4
    )

    total_transactions = int(
        stats_data.get(
            "total",
            0
        )
    )

    fraud_alerts = int(
        stats_data.get(
            "fraud",
            0
        )
    )

    average_risk = float(
        stats_data.get(
            "risk",
            0
        )
    )

    with c1:

        st.metric(
            "My Transactions",
            f"{total_transactions:,}"
        )

    with c2:

        st.metric(
            "Fraud Alerts",
            f"{fraud_alerts:,}"
        )

    with c3:

        st.metric(
            "Average Risk",
            f"{average_risk * 100:.1f}%"
        )

    with c4:

        st.metric(
            "Best Model",
            meta.get(
                "best_model",
                "N/A"
            )
        )

    st.write("")

    with st.container(border=True):

        st.subheader(
            "⚡ Quick Transaction Check"
        )

        st.caption(
            "Enter transaction information to estimate fraud risk."
        )

        with st.form(
            "quick_transaction_form"
        ):

            row1 = st.columns(
                4
            )

            amount = row1[0].number_input(
                "Amount (₹)",
                min_value=1.0,
                max_value=500000.0,
                value=2500.0,
            )

            avg = row1[1].number_input(
                "30-day average (₹)",
                min_value=1.0,
                max_value=500000.0,
                value=1500.0,
            )

            merchant = row1[2].selectbox(
                "Merchant",
                [
                    "Grocery",
                    "Fuel",
                    "Dining",
                    "Shopping",
                    "Electronics",
                    "Travel",
                    "Gaming",
                    "Cash",
                ]
            )

            tx = row1[3].selectbox(
                "Transaction type",
                [
                    "POS",
                    "Online",
                    "Contactless",
                    "ATM",
                    "Mobile",
                ]
            )

            row2 = st.columns(
                4
            )

            hour = row2[0].slider(
                "Transaction hour",
                0,
                23,
                14
            )

            intl = row2[1].selectbox(
                "International",
                [
                    "No",
                    "Yes"
                ]
            )

            card = row2[2].selectbox(
                "Card present",
                [
                    "Yes",
                    "No"
                ]
            )

            velocity = row2[3].number_input(
                "Transactions last hour",
                min_value=0,
                max_value=50,
                value=1,
            )

            submitted = st.form_submit_button(
                "🔎 Analyze Transaction",
                type="primary",
                use_container_width=True,
            )

    if submitted:

        data = {
            "amount": amount,
            "hour": hour,
            "merchant_category": merchant,
            "transaction_type": tx,
            "location_risk": 0.25,
            "device_trust": 0.80,
            "international": int(
                intl == "Yes"
            ),
            "card_present": int(
                card == "Yes"
            ),
            "distance_km": 5.0,
            "velocity_1h": velocity,
            "avg_amount_30d": avg,
            "account_age_days": 800,
            "failed_attempts_24h": 0,
            "previous_fraud_count": 0,
        }

        probability, prediction = predict_transaction(
            data
        )

        if probability is not None:

            try:

                add(
                    user["id"],
                    data,
                    probability,
                    prediction
                )

                st.session_state.result = (
                    probability,
                    prediction
                )

                st.success(
                    "Transaction analyzed and saved."
                )

            except Exception as e:

                st.error(
                    "Prediction completed, but transaction "
                    "could not be saved."
                )

                st.exception(e)

    if st.session_state.result:

        probability, prediction = (
            st.session_state.result
        )

        show_result(
            probability,
            prediction
        )


elif page == "Analyze Transaction":

    st.subheader(
        "🛡️ Analyze Transaction"
    )

    st.caption(
        "Provide transaction context to estimate fraud probability."
    )

    with st.container(border=True):

        with st.form(
            "full_transaction_form"
        ):

            row1 = st.columns(
                4
            )

            amount = row1[0].number_input(
                "Amount (₹)",
                min_value=1.0,
                max_value=500000.0,
                value=2500.0,
            )

            avg = row1[1].number_input(
                "30-day average (₹)",
                min_value=1.0,
                max_value=500000.0,
                value=1500.0,
            )

            merchant = row1[2].selectbox(
                "Merchant category",
                [
                    "Grocery",
                    "Fuel",
                    "Dining",
                    "Shopping",
                    "Electronics",
                    "Travel",
                    "Gaming",
                    "Cash",
                ]
            )

            tx = row1[3].selectbox(
                "Transaction type",
                [
                    "POS",
                    "Online",
                    "Contactless",
                    "ATM",
                    "Mobile",
                ]
            )

            row2 = st.columns(
                4
            )

            hour = row2[0].slider(
                "Transaction hour",
                0,
                23,
                14
            )

            location = row2[1].slider(
                "Location risk",
                0.0,
                1.0,
                0.20
            )

            device = row2[2].slider(
                "Device trust",
                0.0,
                1.0,
                0.85
            )

            distance = row2[3].number_input(
                "Distance from usual location (km)",
                min_value=0.0,
                max_value=5000.0,
                value=5.0,
            )

            row3 = st.columns(
                4
            )

            intl = row3[0].selectbox(
                "International",
                [
                    "No",
                    "Yes"
                ]
            )

            card = row3[1].selectbox(
                "Card present",
                [
                    "Yes",
                    "No"
                ]
            )

            velocity = row3[2].number_input(
                "Transactions last hour",
                min_value=0,
                max_value=50,
                value=1,
            )

            age = row3[3].number_input(
                "Account age (days)",
                min_value=1,
                max_value=10000,
                value=800,
            )

            row4 = st.columns(
                3
            )

            failed = row4[0].number_input(
                "Failed attempts in 24h",
                min_value=0,
                max_value=30,
                value=0,
            )

            previous = row4[1].number_input(
                "Previous fraud alerts",
                min_value=0,
                max_value=50,
                value=0,
            )

            submitted = row4[2].form_submit_button(
                "🛡️ Check Fraud Risk",
                type="primary",
                use_container_width=True,
            )

    if submitted:

        data = {
            "amount": amount,
            "hour": hour,
            "merchant_category": merchant,
            "transaction_type": tx,
            "location_risk": location,
            "device_trust": device,
            "international": int(
                intl == "Yes"
            ),
            "card_present": int(
                card == "Yes"
            ),
            "distance_km": distance,
            "velocity_1h": velocity,
            "avg_amount_30d": avg,
            "account_age_days": age,
            "failed_attempts_24h": failed,
            "previous_fraud_count": previous,
        }

        probability, prediction = predict_transaction(
            data
        )

        if probability is not None:

            try:

                add(
                    user["id"],
                    data,
                    probability,
                    prediction
                )

                st.session_state.result = (
                    probability,
                    prediction
                )

                st.success(
                    "Analysis complete. Transaction saved."
                )

                show_result(
                    probability,
                    prediction
                )

            except Exception as e:

                st.error(
                    "Analysis completed, but transaction "
                    "could not be saved."
                )

                st.exception(e)



elif page == "Transaction History":

    st.subheader(
        " My Transaction History"
    )

    if hist:

        h = pd.DataFrame(
            hist
        )

        if "prediction" in h.columns:

            h["Status"] = h[
                "prediction"
            ].map(
                {
                    0: "✓ Normal",
                    1: "⚠ Fraud"
                }
            )

        if "probability" in h.columns:

            h["Risk"] = h[
                "probability"
            ].apply(
                lambda x:
                f"{float(x) * 100:.2f}%"
            )

        possible_columns = [
            "id",
            "created_at",
            "amount",
            "merchant_category",
            "transaction_type",
            "Risk",
            "Status",
        ]

        display_columns = [
            col
            for col in possible_columns
            if col in h.columns
        ]

        if display_columns:

            st.dataframe(
                h[display_columns],
                use_container_width=True,
                hide_index=True,
            )

        else:

            st.dataframe(
                h,
                use_container_width=True,
                hide_index=True,
            )

        st.write("")

        csv_data = h.to_csv(
            index=False
        )

        st.download_button(
            "⬇ Download my history CSV",
            csv_data,
            "my_transactions.csv",
            "text/csv",
            use_container_width=True,
        )

    else:

        st.info(
            "No transactions yet. "
            "Analyze your first transaction."
        )


elif page == "My Profile":

    st.subheader(
        "👤 My Profile"
    )

    name = (
        user.get("full_name")
        or user.get("username")
        or "User"
    )

    email = user.get(
        "email",
        ""
    )

    username = user.get(
        "username",
        ""
    )

    provider = user.get(
        "auth_provider",
        "local"
    )

    with st.container(border=True):

        st.markdown(
            f"### {name}"
        )

        if email:

            st.caption(
                email
            )

        st.divider()

        p1, p2 = st.columns(
            2
        )

        with p1:

            st.write(
                "**Username**"
            )

            st.write(
                username or "Not available"
            )

        with p2:

            st.write(
                "**Authentication**"
            )

            st.write(
                provider.title()
            )

    st.write("")

    with st.container(border=True):

        st.subheader(
            "Edit profile"
        )

        with st.form(
            "profile_update_form"
        ):

            full_name = st.text_input(
                "Full name",
                value=user.get(
                    "full_name"
                ) or "",
            )

            email = st.text_input(
                "Email",
                value=user.get(
                    "email"
                ) or "",
            )

            st.text_input(
                "Username",
                value=user.get(
                    "username"
                ) or "",
                disabled=True,
            )

            submitted = st.form_submit_button(
                "Save profile",
                type="primary",
            )

        if submitted:

            full_name = full_name.strip()
            email = email.strip()

            if not full_name:

                st.warning(
                    "Full name cannot be empty."
                )

            elif not email:

                st.warning(
                    "Email cannot be empty."
                )

            else:

                try:

                    success = update(
                        user["id"],
                        full_name,
                        email,
                    )

                    if success:

                        st.session_state.user[
                            "full_name"
                        ] = full_name

                        st.session_state.user[
                            "email"
                        ] = email

                        st.success(
                            "Profile updated successfully."
                        )

                        st.rerun()

                    else:

                        st.error(
                            "Could not update profile. "
                            "Email may already be in use."
                        )

                except Exception as e:

                    st.error(
                        "Profile update failed."
                    )

                    st.exception(e)


elif page == "Analytics":

    st.subheader(
        "📈 Personal Analytics"
    )

    if not hist:

        st.info(
            "Analyze transactions to populate your analytics."
        )

    else:

        h = pd.DataFrame(
            hist
        )

        if "probability" not in h.columns:

            st.warning(
                "Risk probability data is not available."
            )

        else:

            c1, c2 = st.columns(
                2
            )

            with c1:

                fig = px.histogram(
                    h,
                    x="probability",
                    nbins=20,
                    title="Risk Distribution",
                )

                fig.update_layout(
                    template="plotly_white",
                    xaxis_title="Fraud Probability",
                    yaxis_title="Transactions",
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True,
                )

            with c2:

                if "merchant_category" in h.columns:

                    merchant_risk = (
                        h.groupby(
                            "merchant_category",
                            as_index=False,
                        )[
                            "probability"
                        ]
                        .mean()
                    )

                    fig = px.bar(
                        merchant_risk,
                        x="merchant_category",
                        y="probability",
                        title="Average Risk by Merchant",
                    )

                    fig.update_layout(
                        template="plotly_white",
                        yaxis_title="Average Probability",
                        xaxis_title="Merchant",
                    )

                    st.plotly_chart(
                        fig,
                        use_container_width=True,
                    )

            if "prediction" in h.columns:

                normal_count = int(
                    (
                        h["prediction"] == 0
                    ).sum()
                )

                fraud_count = int(
                    (
                        h["prediction"] == 1
                    ).sum()
                )

                fig = go.Figure(
                    data=[
                        go.Pie(
                            labels=[
                                "Normal",
                                "Fraud"
                            ],
                            values=[
                                normal_count,
                                fraud_count
                            ],
                            hole=0.55,
                        )
                    ]
                )

                fig.update_layout(
                    title="Transaction Risk Breakdown",
                    template="plotly_white",
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True,
                )

elif page == "Model Performance":

    st.subheader(
        "🤖 Model Performance"
    )

    st.caption(
        "Evaluation metrics from the project's test dataset."
    )

    models_data = meta.get(
        "models",
        {}
    )

    if models_data:

        rows = [
            {
                "Model": name,
                **metrics
            }
            for name, metrics
            in models_data.items()
        ]

        st.dataframe(
            pd.DataFrame(rows),
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.info(
            "Model comparison metrics are not available."
        )

    st.write("")

    test_metrics = meta.get(
        "test_metrics",
        {}
    )

    if test_metrics:

        metric_items = [
            (
                "PR-AUC",
                test_metrics.get(
                    "pr_auc"
                )
            ),
            (
                "ROC-AUC",
                test_metrics.get(
                    "roc_auc"
                )
            ),
            (
                "Precision",
                test_metrics.get(
                    "precision"
                )
            ),
            (
                "Recall",
                test_metrics.get(
                    "recall"
                )
            ),
            (
                "F1",
                test_metrics.get(
                    "f1"
                )
            ),
        ]

        metric_cols = st.columns(
            5
        )

        for col, (label, value) in zip(
            metric_cols,
            metric_items
        ):

            if value is not None:

                col.metric(
                    label,
                    f"{float(value):.4f}"
                )

    st.write("")

    best_model = meta.get(
        "best_model",
        "N/A"
    )

    threshold = float(
        meta.get(
            "threshold",
            0.5
        )
    )

    with st.container(border=True):

        st.subheader(
            "Model Configuration"
        )

        c1, c2 = st.columns(
            2
        )

        with c1:

            st.write(
                "**Best Model**"
            )

            st.info(
                best_model
            )

        with c2:

            st.write(
                "**Decision Threshold**"
            )

            st.info(
                f"{threshold:.3f}"
            )


elif page == "About":

    st.subheader(
        " About FraudGuard AI"
    )

    with st.container(border=True):

        st.title(
            "🛡️ FraudGuard AI"
        )

        st.write(
            "Human-readable credit card fraud detection "
            "powered by machine learning."
        )

        st.divider()

        c1, c2 = st.columns(
            2
        )

        with c1:

            st.write(
                "**Machine Learning**"
            )

            st.write(
                "Logistic Regression + Random Forest + XGBoost"
            )

            st.write("")

            st.write(
                "**Database**"
            )

            st.write(
                "SQLite"
            )

            st.write("")

            st.write(
                "**Authentication**"
            )

            st.write(
                "Google OIDC + bcrypt-secured local accounts"
            )

        with c2:

            st.write(
                "**Best Model**"
            )

            st.write(
                meta.get(
                    "best_model",
                    "N/A"
                )
            )

            st.write("")

            st.write(
                "**Decision Threshold**"
            )

            st.write(
                f"{float(meta.get('threshold', 0.5)):.3f}"
            )

            st.write("")

            st.write(
                "**Purpose**"
            )

            st.write(
                "Analyze transaction behavior and estimate "
                "fraud probability using meaningful transaction "
                "features instead of exposing anonymized "
                "V1–V28 dataset columns."
            )

    st.write("")

    st.caption(
        "FraudGuard AI • Secure Transaction Intelligence"
    )
