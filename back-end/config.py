# config.py
import os
from datetime import timedelta


class Config:
    """기본 설정"""

    # JWT 설정
    JWT_SECRET = os.environ.get('JWT_SECRET', 'fef#ecd@ec21@@ds-asc12!!-ke$dsy')
    TOKEN_EXPIRATION = int(os.environ.get('TOKEN_EXPIRATION', 36000))  # 30분

    # CORS 설정
    CORS_ORIGINS = [
        "*"
    ]

    # 정적 파일 경로
    STATIC_FOLDER = os.path.join(os.path.dirname(__file__), 'app', 'static')
    # STATIC_FOLDER = os.path.join(os.path.dirname(__file__), 'static')
    TEMPLATE_FOLDER = os.path.join(os.path.dirname(__file__), 'app', 'templates')
    # TEMPLATE_FOLDER = os.path.join(os.path.dirname(__file__), 'templates')

    # 로그 설정
    LOG_DIR = "logs"
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'DEBUG')

    # 데이터베이스 설정
    DB_CONFIG = {
        "host": os.environ.get('DB_HOST', 'localhost'),
        "port": int(os.environ.get('DB_PORT', 3306)),
        "user": os.environ.get('DB_USER', 'root'),
        "password": os.environ.get('DB_PASSWORD', '1234'),
        "db": os.environ.get('DB_NAME', 'audit_management'),
        "charset": "utf8mb4",
        "use_unicode": True,
        "init_command": "SET sql_mode='STRICT_TRANS_TABLES', names utf8mb4 COLLATE utf8mb4_unicode_ci",
        "sql_mode": "STRICT_TRANS_TABLES",
    }


class DevelopmentConfig(Config):
    """개발 환경 설정"""
    DEBUG = True


class ProductionConfig(Config):
    """운영 환경 설정"""
    DEBUG = False
    LOG_LEVEL = 'WARNING'


class TestConfig(Config):
    """테스트 환경 설정"""
    TESTING = True


# 환경별 설정 매핑
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestConfig,
    'default': DevelopmentConfig
}