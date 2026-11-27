
from flask import Flask, render_template, request, redirect, url_for, session, Response
import io
import csv
from datetime import date, datetime, timedelta
from db import get_connection
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")
if not app.secret_key:
    raise RuntimeError("FLASK_SECRET_KEY is missing!")

# ==============================
# CONFIG & AUTH
# ==============================

ADMIN_USER = "admin"
ADMIN_PASS = os.getenv("adminPass")

# ==============================
# ROUTES & LOGIC
# ==============================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('logged_in'): 
        return redirect(url_for('index'))
    
    error = None
    if request.method == 'POST':
        if request.form['username'] == ADMIN_USER and request.form['password'] == ADMIN_PASS:
            session['logged_in'] = True
            return redirect(url_for('index'))
        error = "Invalid credentials. Please try again."
    
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
def index():
    if not session.get('logged_in'): 
        return redirect(url_for('login'))
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # 1. Counter Statistics (Excluding General News)
        cursor.execute("SELECT COUNT(*) as count FROM issues WHERE issue != 'General News'")
        total_count = cursor.fetchone()['count']

        today = date.today().strftime('%Y-%m-%d')
        cursor.execute("SELECT COUNT(*) as count FROM issues WHERE DATE(detected_at) = %s AND issue != 'General News'", (today,))
        today_count = cursor.fetchone()['count']

        cursor.execute("SELECT issue, COUNT(*) as cnt FROM issues WHERE issue != 'General News' GROUP BY issue ORDER BY cnt DESC LIMIT 1")
        top_row = cursor.fetchone()
        top_category = top_row['issue'] if top_row else 'N/A'
        top_category_count = top_row['cnt'] if top_row else 0

        # FETCH REAL SOURCE DISTRIBUTION DATA (Excluding General News)
        cursor.execute("SELECT source, COUNT(*) as cnt FROM issues WHERE issue != 'General News' GROUP BY source")
        source_data = cursor.fetchall()
        
        # FETCH REAL CATEGORY BREAKDOWN DATA (Excluding General News)
        cursor.execute("SELECT issue as category, COUNT(*) as cnt FROM issues WHERE issue != 'General News' GROUP BY issue")
        category_data = cursor.fetchall()

        # FETCH LIVE SEVERITY COUNTER FOR NAVBAR BADGE (Excluding General News)
        cursor.execute("SELECT COUNT(*) as count FROM issues WHERE LOWER(severity) = 'high' AND issue != 'General News'")
        critical_count = cursor.fetchone()['count']

        # 2. Extract Query and Filter Parameters
        category_filter = request.args.get('category')
        source_filter   = request.args.get('source')
        search_filter   = request.args.get('search')
        
        # 3. Dynamic SQL Query Builder for the Live Table (Excluding General News)
        query = "SELECT * FROM issues WHERE issue != 'General News' AND department != 'None'"
        params = []

        if category_filter and category_filter != "All":
            query += " AND issue = %s"
            params.append(category_filter)

        if source_filter and source_filter != "All":
            query += " AND source = %s"
            params.append(source_filter)

        if search_filter:
            query += " AND (title LIKE %s OR issue LIKE %s)"
            params.extend([f"%{search_filter}%", f"%{search_filter}%"])

        query += " ORDER BY id DESC LIMIT 50"
        cursor.execute(query, tuple(params))
        issues = cursor.fetchall()

        cursor.close()
        conn.close()

        return render_template(
            'dash.html',
            issues=issues,
            total=total_count,
            today_count=today_count,
            top_category=top_category,
            top_category_count=top_category_count,
            source_data=source_data,        
            category_data=category_data,    
            critical_count=critical_count,
            selected_category=category_filter if category_filter else 'All',
            selected_source=source_filter if source_filter else 'All',
            selected_search=search_filter
        )
    except Exception as e:
        return f"<div style='padding:50px;'><h4>System Registry Parse Error</h4><code>{e}</code></div>"

@app.route('/reports')
def reports():
    if not session.get('logged_in'): 
        return redirect(url_for('login'))
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT DISTINCT department FROM issues WHERE department IS NOT NULL AND department != '' AND department != 'None' AND issue != 'General News'")
        department_list = cursor.fetchall()
        
        cursor.execute("SELECT DISTINCT issue as category FROM issues WHERE issue IS NOT NULL AND issue != '' AND issue != 'General News'")
        category_list = cursor.fetchall()

        # FETCH LIVE SEVERITY COUNTER FOR NAVBAR BADGE
        cursor.execute("SELECT COUNT(*) as count FROM issues WHERE LOWER(severity) = 'high' AND issue != 'General News'")
        critical_count = cursor.fetchone()['count']

        date_filter = request.args.get('date_range', 'All')
        dept_filter = request.args.get('department', 'All')
        cat_filter = request.args.get('category', 'All')
        sev_filter = request.args.get('severity', 'All')

        query = """
                SELECT
                    id,
                    detected_at,
                    severity,
                    issue,
                    location,
                    department,
                    source,
                    link
                FROM issues
                WHERE issue != 'General News'
                AND department != 'None'
            """
        params = []

        if date_filter != "All":
            days = int(date_filter)
            target_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
            query += " AND detected_at >= %s"
            params.append(target_date)

        if dept_filter != "All":
            query += " AND department = %s"
            params.append(dept_filter)

        if cat_filter != "All":
            query += " AND issue = %s"
            params.append(cat_filter)

        if sev_filter != "All":
            query += " AND severity = %s"
            params.append(sev_filter)

        query += " ORDER BY id DESC"
        cursor.execute(query, tuple(params))
        report_issues = cursor.fetchall()

        cursor.close()
        conn.close()

        return render_template(
            'reports.html',
            issues=report_issues,
            department_list=department_list,
            category_list=category_list,
            critical_count=critical_count,
            selected_date=date_filter,
            selected_dept=dept_filter,
            selected_category=cat_filter,
            selected_severity=sev_filter
        )
    except Exception as e:
        return f"<div style='padding:50px;'><h4>Reports Engine Execution Fault Error</h4><code>{e}</code></div>"

@app.route('/analytics')
def analytics():
    if not session.get('logged_in'): 
        return redirect(url_for('login'))
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # 6-Month Rolling Calendar Trend Metrics Query (Strict SQL Mode Compatible)
        trend_query = """
            SELECT 
                CASE 
                    WHEN MONTH(detected_at) = 5 THEN CONCAT('May Wk ', FLOOR((DAY(detected_at) - 1) / 7) + 1)
                    WHEN MONTH(detected_at) = 6 THEN CONCAT('June Wk ', FLOOR((DAY(detected_at) - 1) / 7) + 1)
                END as week_label,
                COUNT(*) as cnt 
            FROM issues 
            WHERE MONTH(detected_at) IN (5, 6) AND YEAR(detected_at) = YEAR(NOW()) AND issue != 'General News'
            GROUP BY 
                CASE 
                    WHEN MONTH(detected_at) = 5 THEN CONCAT('May Wk ', FLOOR((DAY(detected_at) - 1) / 7) + 1)
                    WHEN MONTH(detected_at) = 6 THEN CONCAT('June Wk ', FLOOR((DAY(detected_at) - 1) / 7) + 1)
                END,
                MONTH(detected_at)
            ORDER BY MONTH(detected_at) ASC, week_label ASC
        """
        cursor.execute(trend_query)
        trend_data = cursor.fetchall()

        # Category & Department Frequency Matrix Allocation Dataset
        matrix_query = """
            SELECT issue, department, COUNT(*) as cnt 
            FROM issues 
            WHERE issue != 'General News' AND department != 'None'
            GROUP BY issue, department 
            ORDER BY cnt DESC
        """
        cursor.execute(matrix_query)
        matrix_data = cursor.fetchall()

        # FETCH LIVE SEVERITY COUNTER FOR NAVBAR BADGE
        cursor.execute("SELECT COUNT(*) as count FROM issues WHERE LOWER(severity) = 'high' AND issue != 'General News'")
        critical_count = cursor.fetchone()['count']

        cursor.close()
        conn.close()

        return render_template(
            'analytics.html',
            trend_data=trend_data,
            matrix_data=matrix_data,
            critical_count=critical_count
        )
    except Exception as e:
        return f"<div style='padding:50px;'><h4>Analytics Core Rendering Error Fault</h4><code>{e}</code></div>"

@app.route('/alerts')
def alerts_page():
    if not session.get('logged_in'): 
        return redirect(url_for('login'))
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # Explicitly filtering high severity alerts only
        cursor.execute("SELECT * FROM issues WHERE LOWER(severity) = 'high' AND issue != 'General News' ORDER BY id DESC")
        critical_issues = cursor.fetchall()
        critical_count = len(critical_issues)

        cursor.close()
        conn.close()

        return render_template(
            'alerts.html', 
            critical_issues=critical_issues, 
            critical_count=critical_count
        )
    except Exception as e:
        return f"<div style='padding:50px;'><h4>Alert Center Extraction Error</h4><code>{e}</code></div>"

@app.route('/logs')
def logs():
    if not session.get('logged_in'): 
        return redirect(url_for('login'))
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT COUNT(*) as count FROM issues WHERE issue != 'General News'")
        total_classified = cursor.fetchone()['count']

        # FETCH LIVE SEVERITY COUNTER FOR NAVBAR BADGE
        cursor.execute("SELECT COUNT(*) as count FROM issues WHERE LOWER(severity) = 'high' AND issue != 'General News'")
        critical_count = cursor.fetchone()['count']

        cursor.close()
        conn.close()

        return render_template('logs.html', total_classified=total_classified, critical_count=critical_count)
    except Exception as e:
        return f"<div style='padding:50px;'><h4>System Status Core Rendering Fault</h4><code>{e}</code></div>"

@app.route('/export/csv')
def export_csv():
    if not session.get('logged_in'): 
        return redirect(url_for('login'))
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM issues WHERE issue != 'General News' AND department != 'None'")
        issues = cursor.fetchall()
        cursor.close()
        conn.close()

        output = io.StringIO()
        output.write('\ufeff')

        if issues:
            writer = csv.DictWriter(output, fieldnames=issues[0].keys())
            writer.writeheader()
            writer.writerows(issues)

        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={"Content-Disposition": "attachment;filename=civic_audit_report.csv"}
        )
    except Exception as e:
        return str(e)


if __name__ == '__main__':
    app.run(debug=True, port=5000)