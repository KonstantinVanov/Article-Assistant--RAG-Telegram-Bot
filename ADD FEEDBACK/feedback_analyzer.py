import sqlite3
import pandas as pd
from datetime import datetime, timedelta

def get_feedback_stats(days: int = 7):
    """Получить статистику feedback за указанное количество дней"""
    conn = sqlite3.connect('user_data.db')
    
    query = f"""
    SELECT 
        feedback_type,
        COUNT(*) as count,
        DATE(timestamp) as date
    FROM feedback 
    WHERE timestamp >= date('now', '-{days} days')
    GROUP BY feedback_type, DATE(timestamp)
    ORDER BY date DESC, feedback_type
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    return df

def get_feedback_ratio():
    """Получить соотношение лайков/дизлайков"""
    conn = sqlite3.connect('user_data.db')
    
    query = """
    SELECT 
        feedback_type,
        COUNT(*) as count,
        ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM feedback), 2) as percentage
    FROM feedback 
    GROUP BY feedback_type
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    return df

def export_feedback_to_csv(filename: str = "feedback_export.csv"):
    """Экспортировать все feedback данные в CSV"""
    conn = sqlite3.connect('user_data.db')
    
    query = """
    SELECT 
        f.*,
        u.current_lang as user_language
    FROM feedback f
    LEFT JOIN users u ON f.user_id = u.user_id
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    df.to_csv(filename, index=False, encoding='utf-8')
    return f"Exported {len(df)} records to {filename}"

# Пример использования
if __name__ == "__main__":
    print("Feedback Statistics:")
    print(get_feedback_stats())
    print("\nFeedback Ratio:")
    print(get_feedback_ratio())