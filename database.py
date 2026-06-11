import sqlite3

DB_PATH = "mortgage_app.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mortgages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,

            bank_name TEXT NOT NULL,
            rate REAL NOT NULL,
            term_years INTEGER NOT NULL,
            amount REAL NOT NULL,

            monthly_repayment REAL,
            annual_repayment REAL,
            total_interest_payable REAL,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY(user_id) REFERENCES users(id)
            ON DELETE CASCADE
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,

            annual_income REAL NOT NULL,
            credit_score INTEGER NOT NULL,
            employment_type TEXT NOT NULL,
            monthly_expenses REAL NOT NULL,
            monthly_debts REAL NOT NULL,

            FOREIGN KEY(user_id) REFERENCES users(id)
            ON DELETE CASCADE
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS banks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            max_income_multiple REAL NOT NULL,
            max_ltv REAL NOT NULL,
            min_income REAL NOT NULL,
            accepted_employment_type TEXT NOT NULL,
            active INTEGER DEFAULT 1
        );
    """)

    cursor.execute("""
        INSERT OR IGNORE INTO banks (
            id,
            name,
            max_income_multiple,
            max_ltv,
            min_income,
            accepted_employment_type,
            active
        )
        VALUES
            (1, 'Bank A', 4.5, 90, 25000, 'employed', 1),
            (2, 'Bank B', 5.0, 85, 30000, 'employed', 1),
            (3, 'Bank C', 4.0, 95, 20000, 'self-employed', 1);
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS eligibility_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mortgage_id INTEGER,
            bank_id INTEGER NOT NULL,
            eligible INTEGER NOT NULL,
            reason TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY(mortgage_id) REFERENCES mortgages(id)
            ON DELETE CASCADE,

            FOREIGN KEY(bank_id) REFERENCES banks(id)
            ON DELETE CASCADE
        );
    """)

    cursor.execute("PRAGMA table_info(mortgages)")
    existing_mortgage_columns = [column["name"] for column in cursor.fetchall()]

    if "monthly_repayment" not in existing_mortgage_columns:
        cursor.execute("ALTER TABLE mortgages ADD COLUMN monthly_repayment REAL")

    if "annual_repayment" not in existing_mortgage_columns:
        cursor.execute("ALTER TABLE mortgages ADD COLUMN annual_repayment REAL")

    if "total_interest_payable" not in existing_mortgage_columns:
        cursor.execute("ALTER TABLE mortgages ADD COLUMN total_interest_payable REAL")

    if "created_at" not in existing_mortgage_columns:
        cursor.execute("ALTER TABLE mortgages ADD COLUMN created_at TIMESTAMP")

    cursor.execute("PRAGMA table_info(banks)")
    existing_bank_columns = [column["name"] for column in cursor.fetchall()]

    if "active" not in existing_bank_columns:
        cursor.execute("ALTER TABLE banks ADD COLUMN active INTEGER DEFAULT 1")

    cursor.execute("PRAGMA table_info(eligibility_results)")
    existing_eligibility_columns = [column["name"] for column in cursor.fetchall()]

    if "mortgage_id" not in existing_eligibility_columns:
        cursor.execute("ALTER TABLE eligibility_results ADD COLUMN mortgage_id INTEGER")

    if "created_at" not in existing_eligibility_columns:
        cursor.execute("ALTER TABLE eligibility_results ADD COLUMN created_at TIMESTAMP")

    conn.commit()
    conn.close()


def get_user_profile(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM user_profiles
        WHERE user_id = ?
    """, (user_id,))

    profile = cursor.fetchone()

    conn.close()

    return profile


def save_mortgage_result(
    user_id,
    amount,
    rate,
    term_years,
    monthly_repayment,
    annual_repayment,
    total_interest_payable
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO mortgages (
            user_id,
            bank_name,
            rate,
            term_years,
            amount,
            monthly_repayment,
            annual_repayment,
            total_interest_payable,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    """, (
        user_id,
        "API Mortgage Estimate",
        rate,
        term_years,
        amount,
        monthly_repayment,
        annual_repayment,
        total_interest_payable
    ))

    conn.commit()
    conn.close()


def get_latest_mortgage_summary(user_id, income_multiple=4.5):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        WITH latest AS (
            SELECT
                m.id,
                m.user_id,
                m.bank_name,
                m.amount,
                m.rate,
                m.term_years,
                m.monthly_repayment,
                m.annual_repayment,
                m.total_interest_payable,
                m.created_at,

                up.annual_income,
                up.credit_score,
                up.employment_type,
                up.monthly_expenses,
                up.monthly_debts,

                ? AS income_multiple

            FROM mortgages m

            JOIN user_profiles up
                ON m.user_id = up.user_id

            WHERE m.user_id = ?
              AND m.monthly_repayment IS NOT NULL

            ORDER BY m.created_at DESC, m.id DESC

            LIMIT 1
        ),

        calculated AS (
            SELECT
                *,

                annual_income * income_multiple
                    AS max_borrowing,

                annual_income / 12.0
                    AS monthly_income,

                (annual_income / 12.0) - monthly_expenses - monthly_debts
                    AS monthly_disposable_income,

                amount + total_interest_payable
                    AS total_repayment,

                CASE
                    WHEN ((annual_income / 12.0) - monthly_expenses - monthly_debts) <= 0
                    THEN NULL

                    ELSE (
                        monthly_repayment /
                        ((annual_income / 12.0) - monthly_expenses - monthly_debts)
                    ) * 100
                END AS repayment_percentage

            FROM latest
        )

        SELECT
            *,

            CASE
                WHEN amount > max_borrowing
                THEN 'Not Affordable'

                WHEN monthly_disposable_income <= 0
                THEN 'Not Affordable'

                WHEN repayment_percentage <= 60
                THEN 'Affordable'

                WHEN repayment_percentage <= 75
                THEN 'Review Required'

                ELSE 'Not Affordable'
            END AS affordability_status,

            CASE
                WHEN amount > max_borrowing
                THEN 'The requested loan is higher than your estimated maximum borrowing.'

                WHEN monthly_disposable_income <= 0
                THEN 'Your monthly expenses and debts are equal to or higher than your monthly income.'

                WHEN repayment_percentage <= 60
                THEN 'The repayment is within a safer affordability range.'

                WHEN repayment_percentage <= 75
                THEN 'Warning: the repayment is high compared with your disposable income.'

                ELSE 'Warning: the repayment exceeds the affordability threshold.'
            END AS warning_message,

            'This is an estimate only and not a mortgage offer.'
                AS estimate_note

        FROM calculated;
    """, (
        income_multiple,
        user_id
    ))

    result = cursor.fetchone()

    conn.close()

    return result