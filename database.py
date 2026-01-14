import sqlite3
from flask import session
import bcrypt

DB_NAME = "database.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def execute_select(query, params=()):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def execute_insert(query, params):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        return str(e)

def execute_update(query, params):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        return str(e)

def execute_delete(query, params):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        msg = "Record deleted." if cursor.rowcount else "No record found."
        conn.close()
        return msg
    except Exception as e:
        return str(e)

def check_admin_login(userid, password_input):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tbladminlogin WHERE userid = ?", (userid,))
    user = cursor.fetchone()
    conn.close()

    if user and bcrypt.checkpw(password_input.encode(), user["password"].encode()):
        session["admin_id"] = user["id"]
        session["email"] = user["userid"]
        return True, None
    return False, "Invalid admin credentials"

def check_user_login(userid, password_input):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tblusers WHERE email = ?", (userid,))
    user = cursor.fetchone()
    conn.close()

    if user and bcrypt.checkpw(password_input.encode(), user["password"].encode()):
        session["id"] = user["id"]
        session["email"] = user["email"]
        return True, None
    return False, "Invalid user credentials"