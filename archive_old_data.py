from db import get_connection

def archive_and_clear_db():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        print("📦 Archiving existing articles and issues...")

        # Copy data from operational tables into archive tables
        cursor.execute("INSERT INTO articles_archive SELECT * FROM articles;")
        cursor.execute("INSERT INTO issues_archive SELECT * FROM issues;")

        # Clear active tables so daily scraper starts fresh
        cursor.execute("DELETE FROM articles;")
        cursor.execute("DELETE FROM issues;")

        conn.commit()
        print("✅ Success! Historical records moved to archive tables.")
        print("🧹 Main operational tables ('articles' and 'issues') are now empty and ready for fresh daily scraping.")

    except Exception as e:
        conn.rollback()
        print(f"❌ Archiving failed: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    confirm = input("⚠️ Are you sure you want to archive all current data and clear active tables? (y/n): ")
    if confirm.lower() == 'y':
        archive_and_clear_db()