# app/__init__.py
import logging
import os
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from config import config


def create_app(config_name=None):
    """Flask 애플리케이션 팩토리"""

    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "default")

    app = Flask(
        __name__,
        static_folder=config[config_name].STATIC_FOLDER,
        static_url_path="",
        template_folder=config[config_name].TEMPLATE_FOLDER,
    )

    # 설정 로드
    app.config.from_object(config[config_name])

    # CORS 설정
    CORS(
        app,
        resources={r"/api/*": {
            "origins": "*",
            "supports_credentials": True,
        }},
        allow_headers=["Content-Type", "Authorization"],
        expose_headers=["Content-Type", "Authorization"],
        max_age=600,
    )

    # 로깅 설정
    setup_logging(app)

    # 컨트롤러 등록
    register_controllers(app)

    # 에러 핸들러 등록
    register_error_handlers(app)

    # Vue SPA 라우팅 설정
    setup_spa_routing(app)

    return app


def setup_logging(app):
    """로깅 설정"""
    os.makedirs(app.config["LOG_DIR"], exist_ok=True)

    logging.basicConfig(
        level=getattr(logging, app.config["LOG_LEVEL"]),
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(os.path.join(app.config["LOG_DIR"], "server.log"),
                                encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def register_controllers(app):
    """컨트롤러 등록"""
    from app.controllers.auth_controller import auth_bp
    from app.controllers.security_audit_controller import audit_bp
    from app.controllers.security_education_controller import education_bp
    from app.controllers.phishing_training_controller import training_bp
    from app.controllers.total_score_controller import score_bp
    from app.controllers.admin_exception_controller import exception_bp
    from app.controllers.manual_check_controller import manual_check_bp
    from app.controllers.manual_check_period_controller import (
        manual_check_period_bp, )  # 추가

    from app.controllers.personal_dashboard_controller import personal_dashboard_bp
    from app.controllers.admin_personal_score_controller import admin_personal_score_bp

    from app.controllers.admin_dashboard_controller import admin_dashboard_bp
    from app.controllers.admin_user_management_controller import admin_user_management_bp
    from app.controllers.admin_user_detail_controller import admin_user_detail_bp
    from app.controllers.admin_batch_controller import admin_batch_bp
    # 새로 추가된 사용자 CRUD 컨트롤러
    from app.controllers.admin_user_controller import admin_user_bp
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(audit_bp, url_prefix="/api/security-audit")
    app.register_blueprint(education_bp, url_prefix="/api/security-education")
    app.register_blueprint(training_bp, url_prefix="/api/phishing-training")
    app.register_blueprint(score_bp, url_prefix="/api/security-score")
    app.register_blueprint(exception_bp, url_prefix="/api/exceptions")
    app.register_blueprint(manual_check_bp, url_prefix="/api/manual-check")  # 새로 추가
    app.register_blueprint(manual_check_period_bp, url_prefix="/api/manual-check")  # 추가

    app.register_blueprint(
        personal_dashboard_bp,
        url_prefix="/api/personal-dashboard")  # url_prefix는 블루프린트에서 이미 설정됨
    app.register_blueprint(admin_personal_score_bp,
                           url_prefix="/api/admin/personal-scores")

    app.register_blueprint(admin_dashboard_bp)
    app.register_blueprint(admin_user_management_bp)
    app.register_blueprint(admin_user_detail_bp)

    app.register_blueprint(admin_batch_bp)
    # 새로운 사용자 CRUD API 등록
    app.register_blueprint(admin_user_bp)  # url_prefix는 이미 블루프린트에서 설정됨

def register_error_handlers(app):
    """에러 핸들러 등록"""

    @app.errorhandler(404)
    def not_found(error):
        # API 요청인 경우
        if request.path.startswith("/api/"):
            return jsonify({"error": "API endpoint not found"}), 404

        # Vue 앱으로 라우팅
        try:
            return send_from_directory(app.static_folder, "index.html")
        except FileNotFoundError:
            return "Vue app not found", 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({"error": "Internal server error"}), 500


def setup_spa_routing(app):
    """Vue SPA 라우팅 설정"""

    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_vue_app(path):
        # API 경로는 제외
        if path.startswith("api/"):
            return jsonify({"error": "API endpoint not found"}), 404

        # 정적 파일 요청 처리
        if "." in path:
            try:
                return send_from_directory(app.static_folder, path)
            except FileNotFoundError:
                pass

        # SPA 라우팅을 위해 index.html 반환
        try:
            return send_from_directory(app.static_folder, "index.html")
        except FileNotFoundError:
            return "Vue app not found. Please build the Vue project first.", 404
