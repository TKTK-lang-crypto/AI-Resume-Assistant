# utils/db.py
import sqlite3
import datetime

DB_PATH = "history.db"

def init_db():
    """初始化数据库，创建表（如果不存在）"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS analysis_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            analysis_type TEXT NOT NULL,
            resume_text TEXT NOT NULL,
            job_description TEXT NOT NULL,
            result TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def save_record(analysis_type: str, resume_text: str, job_description: str, result: str):
    """保存一条分析记录"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.datetime.now().isoformat()
    c.execute('''
        INSERT INTO analysis_history (analysis_type, resume_text, job_description, result, created_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (analysis_type, resume_text, job_description, result, now))
    conn.commit()
    conn.close()

def get_all_records(limit=50):
    """获取所有记录，按时间倒序，返回列表 of dict"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('''
        SELECT id, analysis_type, resume_text, job_description, result, created_at
        FROM analysis_history
        ORDER BY created_at DESC
        LIMIT ?
    ''', (limit,))
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def delete_record(record_id: int):
    """删除指定记录"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM analysis_history WHERE id = ?', (record_id,))
    conn.commit()
    conn.close()

def clear_all_records():
    """清空所有记录"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM analysis_history')
    conn.commit()
    conn.close()