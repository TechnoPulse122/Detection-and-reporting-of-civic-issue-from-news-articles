

import pymysql
from dotenv import load_dotenv
import os

load_dotenv()

# ==============================
# DATABASE CONFIGURATION
# ==============================

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("dbuser"),
    "password": os.getenv("dbpassword"),
    "database": os.getenv("DB_NAME"),
    "charset": "utf8mb4",
    "use_unicode": True,
    "ssl": {"check_hostname": False},
    "connect_timeout": 10
}

# ==============================
# CONNECTION
# ==============================

def get_connection():
    conn = pymysql.connect(**DB_CONFIG)
    return conn

# ==============================
# CONFIGURATION
# ==============================


# ==============================
# INITIALIZE TABLES
# ==============================
def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Create tables with MySQL compatible syntax
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id         INTEGER PRIMARY KEY AUTO_INCREMENT,
            title      TEXT NOT NULL,
            link       VARCHAR(500) UNIQUE NOT NULL,
            content    LONGTEXT,
            source     VARCHAR(100),
            scraped_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS processed_articles (
            id              INT PRIMARY KEY AUTO_INCREMENT,
            article_id      INT NOT NULL UNIQUE,
            cleaned_title   TEXT,
            cleaned_content LONGTEXT,
            entities        JSON,
            summary         TEXT,
            civic_score     FLOAT,
            matched_terms   JSON,
            processed_at    DATETIME DEFAULT CURRENT_TIMESTAMP,

        INDEX idx_processed_at (processed_at)
        );
    """)   
    # Updated severity column structure to use ENUM data-type mapping 
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS issues (
            id          INTEGER PRIMARY KEY AUTO_INCREMENT,
            article_id  INTEGER,
            title       TEXT,
            link        VARCHAR(500),
            source      VARCHAR(100),
            issue       VARCHAR(200),
            department  VARCHAR(200),
            severity    ENUM('Low', 'Medium', 'High') DEFAULT 'Medium',
            location    VARCHAR(100) DEFAULT 'Ludhiana',
            detected_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)


    

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS email_log (
            id       INTEGER PRIMARY KEY AUTO_INCREMENT,
            issue_id INTEGER,
            receiver VARCHAR(255),
            subject  VARCHAR(255),
            status   VARCHAR(100),
            sent_at  DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Archive tables for historical data storage
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS articles_archive LIKE articles;
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS issues_archive LIKE issues;
    """)
    conn.commit()
    cursor.close()
    conn.close()
    print("✅ Database initialized (MySQL).")

# ==============================
# INSERT FUNCTIONS
# ==============================
def insert_article(title, link, content, source):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        query = """
            INSERT IGNORE INTO articles (title, link, content, source)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (title, link, content, source))
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        print(f" ❌ DB insert article error: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def check_link_exists(link):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM articles WHERE link = %s", (link,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row is not None

def insert_issue(article_id, title, link, source, issue, department, 
                 severity="Medium", location="Ludhiana"):
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check if a dynamic None or empty value was explicitly passed by the classifier.
    # If so, intercept it and replace it with your fallback default string here.
    if not location:
        location = "Ludhiana"
        
    try:
        query = """
            INSERT INTO issues 
                (article_id, title, link, source, issue, department, severity, location)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (article_id, title, link, source, issue, department, severity, location))
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        print(f" ❌ DB insert issue error: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

#updation1
def update_issue_classification(
    issue_id,
    issue,
    department,
    severity,
    location
):
    """
    Safely updates an EXISTING issue row.

    Does NOT create or delete rows.
    Only updates classification fields.
    """

    conn = get_connection()
    cursor = conn.cursor()

    try:
        query = """
            UPDATE issues
            SET
                issue = %s,
                department = %s,
                severity = %s,
                location = %s
            WHERE id = %s
        """

        cursor.execute(
            query,
            (issue, department, severity, location, issue_id)
        )

        conn.commit()

        # Successful execution = successful update.
        # rowcount can be 0 when the values were already identical.
        return True

    except Exception as e:
        conn.rollback()
        print(f" ❌ DB update issue error: {e}")
        return False

    finally:
        cursor.close()
        conn.close()
#-------------------------------------------------------------------------------

def log_email(issue_id, receiver, subject, status):
    conn = get_connection()
    cursor = conn.cursor()
    query = """
        INSERT INTO email_log (issue_id, receiver, subject, status)
        VALUES (%s, %s, %s, %s)
    """
    cursor.execute(query, (issue_id, receiver, subject, status))
    conn.commit()
    cursor.close()
    conn.close()

    

if __name__ == "__main__":
    init_db()