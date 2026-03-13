# app/utils/database.py
import pymysql
from flask import current_app
from contextlib import contextmanager


class DatabaseManager:
    """데이터베이스 연결 관리 클래스"""

    @staticmethod
    def get_connection():
        """데이터베이스 연결 생성"""
        config = current_app.config['DB_CONFIG'].copy()
        config['cursorclass'] = pymysql.cursors.DictCursor
        return pymysql.connect(**config)

    @staticmethod
    @contextmanager
    def get_db_connection():
        """컨텍스트 매니저를 사용한 안전한 데이터베이스 연결"""
        conn = None
        try:
            conn = DatabaseManager.get_connection()
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close()

    @staticmethod
    @contextmanager
    def get_db_cursor(commit=True):
        """커서를 포함한 컨텍스트 매니저"""
        with DatabaseManager.get_db_connection() as conn:
            try:
                with conn.cursor() as cursor:
                    yield cursor
                    if commit:
                        conn.commit()
            except Exception as e:
                conn.rollback()
                raise e


# 편의 함수들
def get_db_connection():
    """간단한 데이터베이스 연결 함수"""
    return DatabaseManager.get_connection()


def execute_query(query, params=None, fetch_one=False, fetch_all=False):
    """수정된 쿼리 실행 헬퍼 함수"""
    # print(f"[DB_DEBUG] 쿼리: {query}")
    # print(f"[DB_DEBUG] 파라미터: {params}")

    with DatabaseManager.get_db_cursor() as cursor:
        cursor.execute(query, params or [])

        query_type = query.strip().upper()

        if query_type.startswith('SELECT'):
            if fetch_one:
                result = cursor.fetchone()
                print(f"[DB_DEBUG] fetchone 결과: {result}")
                return result
            elif fetch_all:  # 이 조건 추가!
                result = cursor.fetchall()
                print(f"[DB_DEBUG] fetchall 결과: {len(result) if result else 0}건")
                return result
            else:
                # 기본적으로 fetchall() 실행
                result = cursor.fetchall()
                print(f"[DB_DEBUG] fetchall 결과: {len(result) if result else 0}건")
                return result
        else:
            affected_rows = cursor.rowcount
            print(f"[DB_DEBUG] 영향받은 행 수: {affected_rows}")
            return affected_rows


def execute_many(query, params_list):
    """배치 쿼리 실행 함수"""
    with DatabaseManager.get_db_cursor() as cursor:
        return cursor.executemany(query, params_list)
