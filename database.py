import mysql.connector
from mysql.connector import Error
from config import Config


def create_database_if_not_exists():
    conn = mysql.connector.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD
    )
    cursor = conn.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {Config.MYSQL_DB}")
    conn.commit()
    cursor.close()
    conn.close()


def get_connection():
    return mysql.connector.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DB
    )


def init_db():
    create_database_if_not_exists()

    conn = get_connection()
    cursor = conn.cursor()

    # 1) USERS TABLE (must exist before FKs reference it)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        );
    """)

    # 2) USER PROFILES (FK -> users)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_profiles (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT UNIQUE NOT NULL,
            annual_income DECIMAL(12,2) NOT NULL,
            credit_score INT NOT NULL,
            employment_type VARCHAR(50) NOT NULL,
            monthly_expenses DECIMAL(12,2) NOT NULL,
            monthly_debts DECIMAL(12,2) NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
    """)

    # 3) MORTGAGES (FK -> users)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mortgages (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            bank_name VARCHAR(255) NOT NULL,
            rate DECIMAL(6,3) NOT NULL,
            term_years INT NOT NULL,
            amount DECIMAL(12,2) NOT NULL,
            monthly_repayment DECIMAL(12,2),
            annual_repayment DECIMAL(12,2),
            total_interest_payable DECIMAL(12,2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
    """)

    # 4) BANKS (independent)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS banks (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            max_income_multiple DECIMAL(4,2) NOT NULL,
            max_ltv DECIMAL(5,2) NOT NULL,
            min_income DECIMAL(12,2) NOT NULL,
            accepted_employment_type VARCHAR(50) NOT NULL,
            active TINYINT DEFAULT 1
        );
    """)

    cursor.execute("""
    INSERT INTO banks
    (id, name, max_income_multiple, max_ltv, min_income, accepted_employment_type, active)
    VALUES
    (1, 'HSBC', 4.5, 90, 25000, 'employed', 1),
    (2, 'Barclays', 4.75, 85, 30000, 'employed', 1),
    (3, 'Lloyds Bank', 4.5, 90, 22000, 'employed', 1),
    (4, 'NatWest', 4.25, 85, 24000, 'employed', 1),
    (5, 'Santander', 5.0, 80, 30000, 'employed', 1),
    (6, 'Halifax', 4.5, 95, 20000, 'employed', 1),
    (7, 'Nationwide', 4.75, 90, 25000, 'self-employed', 1),
    (8, 'TSB', 4.0, 85, 21000, 'employed', 1),
    (9, 'Virgin Money', 4.25, 90, 26000, 'self-employed', 1),
    (10, 'Metro Bank', 4.0, 80, 23000, 'employed', 1)
    ON DUPLICATE KEY UPDATE
        name = VALUES(name),
        max_income_multiple = VALUES(max_income_multiple),
        max_ltv = VALUES(max_ltv),
        min_income = VALUES(min_income),
        accepted_employment_type = VALUES(accepted_employment_type),
        active = VALUES(active);
    """)

    # 5) ELIGIBILITY RESULTS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS eligibility_results (
            id INT AUTO_INCREMENT PRIMARY KEY,
            mortgage_id INT,
            bank_id INT NOT NULL,
            eligible TINYINT NOT NULL,
            reason TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (mortgage_id) REFERENCES mortgages(id) ON DELETE CASCADE,
            FOREIGN KEY (bank_id) REFERENCES banks(id) ON DELETE CASCADE
        );
    """)

    conn.commit()
    cursor.close()
    conn.close()


def get_user_profile(user_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM user_profiles
        WHERE user_id = %s
    """, (user_id,))

    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result


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
            total_interest_payable
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
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
    cursor.close()
    conn.close()


def get_latest_mortgage_summary(user_id, income_multiple=4.5):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

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

                %s AS income_multiple

            FROM mortgages m
            JOIN user_profiles up ON m.user_id = up.user_id
            WHERE m.user_id = %s
              AND m.monthly_repayment IS NOT NULL
            ORDER BY m.created_at DESC, m.id DESC
            LIMIT 1
        ),

        calculated AS (
            SELECT
                *,
                annual_income * income_multiple AS max_borrowing,
                annual_income / 12.0 AS monthly_income,
                (annual_income / 12.0) - monthly_expenses - monthly_debts AS monthly_disposable_income,
                amount + total_interest_payable AS total_repayment,

                CASE
                    WHEN ((annual_income / 12.0) - monthly_expenses - monthly_debts) <= 0
                    THEN NULL
                    ELSE (monthly_repayment /
                         ((annual_income / 12.0) - monthly_expenses - monthly_debts)) * 100
                END AS repayment_percentage
            FROM latest
        )

        SELECT
            *,
            CASE
                WHEN amount > max_borrowing THEN 'Not Affordable'
                WHEN monthly_disposable_income <= 0 THEN 'Not Affordable'
                WHEN repayment_percentage <= 60 THEN 'Affordable'
                WHEN repayment_percentage <= 75 THEN 'Review Required'
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

            'This is an estimate only and not a mortgage offer.' AS estimate_note

        FROM calculated;
    """, (income_multiple, user_id))

    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result
