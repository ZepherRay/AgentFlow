import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pymysql
from config import settings

def run_migration():
    print("Connecting to database...")
    connection = pymysql.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        database=settings.DB_NAME,
        charset='utf8mb4'
    )
    
    try:
        with connection.cursor() as cursor:
            sql_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "001_add_agent_columns_and_skills.sql")
            print(f"Reading SQL file: {sql_file}")
            
            with open(sql_file, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            sql_statements = sql_content.split(';')
            
            for idx, statement in enumerate(sql_statements):
                statement = statement.strip()
                if statement:
                    print(f"Executing statement {idx + 1}...")
                    try:
                        cursor.execute(statement)
                        connection.commit()
                        print(f"Statement {idx + 1} executed successfully")
                    except Exception as e:
                        print(f"Error executing statement {idx + 1}: {e}")
                        connection.rollback()
                        raise
        
        print("\n✅ Migration completed successfully!")
        
    finally:
        connection.close()

if __name__ == "__main__":
    run_migration()