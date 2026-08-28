
# ============================================================
# FRAUDGUARD AI - DATABASE
# ============================================================

import sqlite3
import bcrypt
import re

from pathlib import Path
from datetime import datetime


# ============================================================
# DATABASE CONFIG
# ============================================================

ROOT = Path(__file__).resolve().parent

DB_PATH = ROOT / "fraudguard.db"


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_conn():

    conn = sqlite3.connect(
        DB_PATH,
        timeout=10
    )

    conn.row_factory = sqlite3.Row

    # Foreign keys enable
    conn.execute(
        "PRAGMA foreign_keys = ON"
    )

    return conn


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def init_db():

    conn = get_conn()

    try:

        # ====================================================
        # USERS TABLE
        # ====================================================

        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                username TEXT UNIQUE,

                email TEXT UNIQUE NOT NULL,

                password_hash TEXT,

                full_name TEXT,

                auth_provider TEXT DEFAULT 'local',

                google_sub TEXT UNIQUE,

                profile_picture TEXT,

                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ====================================================
        # TRANSACTIONS TABLE
        # ====================================================

        conn.execute("""
            CREATE TABLE IF NOT EXISTS transactions (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER NOT NULL,

                amount REAL,

                hour INTEGER,

                merchant_category TEXT,

                transaction_type TEXT,

                location_risk REAL,

                device_trust REAL,

                international INTEGER DEFAULT 0,

                card_present INTEGER DEFAULT 1,

                distance_km REAL,

                velocity_1h INTEGER,

                avg_amount_30d REAL,

                account_age_days INTEGER,

                failed_attempts_24h INTEGER,

                previous_fraud_count INTEGER,

                probability REAL,

                prediction INTEGER,

                created_at TEXT DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY(user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE
            )
        """)

        conn.commit()

        # ====================================================
        # USERS MIGRATION
        # ====================================================

        user_columns = {
            row["name"]
            for row in conn.execute(
                "PRAGMA table_info(users)"
            ).fetchall()
        }

        user_migrations = {

            "password_hash":
                "TEXT",

            "full_name":
                "TEXT",

            "auth_provider":
                "TEXT DEFAULT 'local'",

            "google_sub":
                "TEXT",

            "profile_picture":
                "TEXT",

            "created_at":
                "TEXT DEFAULT CURRENT_TIMESTAMP",
        }

        for column, definition in user_migrations.items():

            if column not in user_columns:

                conn.execute(
                    f"""
                    ALTER TABLE users
                    ADD COLUMN {column} {definition}
                    """
                )

        # ====================================================
        # TRANSACTIONS MIGRATION
        # ====================================================

        transaction_columns = {
            row["name"]
            for row in conn.execute(
                "PRAGMA table_info(transactions)"
            ).fetchall()
        }

        transaction_migrations = {

            "user_id":
                "INTEGER",

            "amount":
                "REAL",

            "hour":
                "INTEGER",

            "merchant_category":
                "TEXT",

            "transaction_type":
                "TEXT",

            "location_risk":
                "REAL",

            "device_trust":
                "REAL",

            "international":
                "INTEGER DEFAULT 0",

            "card_present":
                "INTEGER DEFAULT 1",

            "distance_km":
                "REAL",

            "velocity_1h":
                "INTEGER",

            "avg_amount_30d":
                "REAL",

            "account_age_days":
                "INTEGER",

            "failed_attempts_24h":
                "INTEGER",

            "previous_fraud_count":
                "INTEGER",

            "probability":
                "REAL",

            "prediction":
                "INTEGER",

            "created_at":
                "TEXT DEFAULT CURRENT_TIMESTAMP",
        }

        for column, definition in transaction_migrations.items():

            if column not in transaction_columns:

                conn.execute(
                    f"""
                    ALTER TABLE transactions
                    ADD COLUMN {column} {definition}
                    """
                )

        conn.commit()

    finally:

        conn.close()


# ============================================================
# NORMALIZATION
# ============================================================

def normalize_email(email):

    return (
        email or ""
    ).strip().lower()


def normalize_username(username):

    return (
        username or ""
    ).strip().lower()


# ============================================================
# USERNAME VALIDATION
# ============================================================

def valid_username(username):

    return bool(
        re.match(
            r"^[a-zA-Z0-9_.-]{3,30}$",
            username or ""
        )
    )


# ============================================================
# PASSWORD HASH
# ============================================================

def hash_password(password):

    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")


# ============================================================
# PASSWORD VERIFY
# ============================================================

def verify_password(
    password,
    password_hash
):

    if not password_hash:

        return False

    try:

        return bcrypt.checkpw(
            password.encode("utf-8"),
            password_hash.encode("utf-8")
        )

    except Exception:

        return False


# ============================================================
# LOCAL USER REGISTER
# ============================================================

def register(
    username,
    email,
    password,
    full_name
):

    username = normalize_username(
        username
    )

    email = normalize_email(
        email
    )

    full_name = (
        full_name or ""
    ).strip()

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    if not valid_username(username):

        return False

    if not email or "@" not in email:

        return False

    if len(password or "") < 6:

        return False

    # --------------------------------------------------------
    # Password hash
    # --------------------------------------------------------

    password_hash = hash_password(
        password
    )

    conn = get_conn()

    try:

        conn.execute("""
            INSERT INTO users
            (
                username,
                email,
                password_hash,
                full_name,
                auth_provider
            )

            VALUES
            (
                ?,
                ?,
                ?,
                ?,
                'local'
            )
        """, (
            username,
            email,
            password_hash,
            full_name
        ))

        conn.commit()

        return True

    except sqlite3.IntegrityError:

        return False

    finally:

        conn.close()


# ============================================================
# LOCAL LOGIN
# ============================================================

def login(
    identifier,
    password
):

    identifier = (
        identifier or ""
    ).strip()

    conn = get_conn()

    try:

        row = conn.execute("""
            SELECT *
            FROM users

            WHERE
                lower(username) = lower(?)

                OR

                lower(email) = lower(?)

            LIMIT 1
        """, (
            identifier,
            identifier
        )).fetchone()

    finally:

        conn.close()

    if not row:

        return None

    # --------------------------------------------------------
    # Google account does not have password
    # --------------------------------------------------------

    if not row["password_hash"]:

        return None

    # --------------------------------------------------------
    # Verify password
    # --------------------------------------------------------

    if not verify_password(
        password,
        row["password_hash"]
    ):

        return None

    return dict(row)


# ============================================================
# GOOGLE LOGIN / REGISTER
# ============================================================

def google_login_or_register(
    google_sub,
    email,
    name="",
    picture=""
):

    google_sub = str(
        google_sub or ""
    ).strip()

    email = normalize_email(
        email
    )

    name = (
        name or ""
    ).strip()

    picture = (
        picture or ""
    ).strip()

    if not google_sub or not email:

        return None

    conn = get_conn()

    try:

        # ====================================================
        # FIND BY GOOGLE SUB
        # ====================================================

        row = conn.execute("""
            SELECT *
            FROM users

            WHERE google_sub = ?

            LIMIT 1
        """, (
            google_sub,
        )).fetchone()

        if row:

            conn.execute("""
                UPDATE users

                SET
                    full_name = ?,
                    email = ?,
                    profile_picture = ?,
                    auth_provider = 'google'

                WHERE id = ?
            """, (
                name or row["full_name"],
                email,
                picture or row["profile_picture"],
                row["id"]
            ))

            conn.commit()

            updated = conn.execute("""
                SELECT *
                FROM users

                WHERE id = ?

                LIMIT 1
            """, (
                row["id"],
            )).fetchone()

            return dict(updated)

        # ====================================================
        # FIND BY EMAIL
        # ====================================================

        row = conn.execute("""
            SELECT *
            FROM users

            WHERE lower(email) = lower(?)

            LIMIT 1
        """, (
            email,
        )).fetchone()

        if row:

            conn.execute("""
                UPDATE users

                SET
                    google_sub = ?,
                    profile_picture = ?,
                    auth_provider = 'google',
                    full_name = ?

                WHERE id = ?
            """, (
                google_sub,
                picture or row["profile_picture"],
                name or row["full_name"],
                row["id"]
            ))

            conn.commit()

            updated = conn.execute("""
                SELECT *
                FROM users

                WHERE id = ?

                LIMIT 1
            """, (
                row["id"],
            )).fetchone()

            return dict(updated)

        # ====================================================
        # CREATE NEW GOOGLE USER
        # ====================================================

        base_username = normalize_username(
            email.split("@")[0]
        )

        # Google email se username invalid ho
        if not valid_username(
            base_username
        ):

            base_username = "googleuser"

        username = base_username

        counter = 1

        # ----------------------------------------------------
        # Make username unique
        # ----------------------------------------------------

        while True:

            exists = conn.execute("""
                SELECT id

                FROM users

                WHERE lower(username) = lower(?)

                LIMIT 1
            """, (
                username,
            )).fetchone()

            if not exists:

                break

            username = (
                f"{base_username}{counter}"
            )

            counter += 1

        # ----------------------------------------------------
        # Insert Google user
        # ----------------------------------------------------

        conn.execute("""
            INSERT INTO users
            (
                username,
                email,
                password_hash,
                full_name,
                auth_provider,
                google_sub,
                profile_picture
            )

            VALUES
            (
                ?,
                ?,
                NULL,
                ?,
                'google',
                ?,
                ?
            )
        """, (
            username,
            email,
            name,
            google_sub,
            picture
        ))

        conn.commit()

        user = conn.execute("""
            SELECT *
            FROM users

            WHERE google_sub = ?

            LIMIT 1
        """, (
            google_sub,
        )).fetchone()

        return dict(user)

    except sqlite3.IntegrityError:

        # ----------------------------------------------------
        # Rare case:
        # Google account/email collision
        # ----------------------------------------------------

        row = conn.execute("""
            SELECT *
            FROM users

            WHERE
                lower(email) = lower(?)

                OR

                google_sub = ?

            LIMIT 1
        """, (
            email,
            google_sub
        )).fetchone()

        if row:

            return dict(row)

        return None

    finally:

        conn.close()


# ============================================================
# ADD TRANSACTION
# ============================================================

def add(
    user_id,
    data,
    probability,
    prediction
):

    conn = get_conn()

    try:

        conn.execute("""
            INSERT INTO transactions
            (
                user_id,

                amount,
                hour,

                merchant_category,
                transaction_type,

                location_risk,
                device_trust,

                international,
                card_present,

                distance_km,
                velocity_1h,

                avg_amount_30d,

                account_age_days,

                failed_attempts_24h,

                previous_fraud_count,

                probability,
                prediction,

                created_at
            )

            VALUES
            (
                ?,

                ?,
                ?,

                ?,
                ?,

                ?,
                ?,

                ?,
                ?,

                ?,
                ?,

                ?,

                ?,

                ?,

                ?,

                ?,
                ?,

                ?
            )
        """, (

            user_id,

            data.get(
                "amount",
                0
            ),

            data.get(
                "hour",
                0
            ),

            data.get(
                "merchant_category",
                ""
            ),

            data.get(
                "transaction_type",
                ""
            ),

            data.get(
                "location_risk",
                0
            ),

            data.get(
                "device_trust",
                0
            ),

            data.get(
                "international",
                0
            ),

            data.get(
                "card_present",
                1
            ),

            data.get(
                "distance_km",
                0
            ),

            data.get(
                "velocity_1h",
                0
            ),

            data.get(
                "avg_amount_30d",
                0
            ),

            data.get(
                "account_age_days",
                0
            ),

            data.get(
                "failed_attempts_24h",
                0
            ),

            data.get(
                "previous_fraud_count",
                0
            ),

            float(probability),

            int(prediction),

            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        ))

        conn.commit()

    finally:

        conn.close()


# ============================================================
# TRANSACTION HISTORY
# ============================================================

def history(user_id):

    conn = get_conn()

    try:

        rows = conn.execute("""
            SELECT *

            FROM transactions

            WHERE user_id = ?

            ORDER BY id DESC
        """, (
            user_id,
        )).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:

        conn.close()


# ============================================================
# USER STATISTICS
# ============================================================

def stats(user_id):

    conn = get_conn()

    try:

        # ----------------------------------------------------
        # Total transactions
        # ----------------------------------------------------

        total = conn.execute("""
            SELECT COUNT(*)

            FROM transactions

            WHERE user_id = ?
        """, (
            user_id,
        )).fetchone()[0]

        # ----------------------------------------------------
        # Fraud transactions
        # ----------------------------------------------------

        fraud = conn.execute("""
            SELECT COUNT(*)

            FROM transactions

            WHERE
                user_id = ?

                AND prediction = 1
        """, (
            user_id,
        )).fetchone()[0]

        # ----------------------------------------------------
        # Average fraud probability
        # ----------------------------------------------------

        risk = conn.execute("""
            SELECT
                COALESCE(
                    AVG(probability),
                    0
                )

            FROM transactions

            WHERE user_id = ?
        """, (
            user_id,
        )).fetchone()[0]

        return {

            "total":
                int(total or 0),

            "fraud":
                int(fraud or 0),

            "risk":
                float(risk or 0)
        }

    finally:

        conn.close()


# ============================================================
# UPDATE USER PROFILE
# ============================================================

def update(
    user_id,
    full_name,
    email
):

    full_name = (
        full_name or ""
    ).strip()

    email = normalize_email(
        email
    )

    if not email or "@" not in email:

        return False

    conn = get_conn()

    try:

        conn.execute("""
            UPDATE users

            SET
                full_name = ?,
                email = ?

            WHERE id = ?
        """, (
            full_name,
            email,
            user_id
        ))

        conn.commit()

        return True

    except sqlite3.IntegrityError:

        return False

    finally:

        conn.close()


# ============================================================
# INITIALIZE DATABASE
# ============================================================

init_db()


# ============================================================
# DIRECT TEST
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 55)
    print(" FraudGuard AI - Database")
    print("=" * 55)
    print(f"Database location: {DB_PATH}")
    print("Database initialized successfully.")
    print("Migration completed successfully.")
    print("=" * 55)

