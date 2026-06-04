from flask import Flask, jsonify
from flask_cors import CORS

from routes.user import user_bp
from routes.dataset import dataset_bp
from routes.query import query_bp


def create_app():
    app = Flask(__name__)
    CORS(app)

    app.register_blueprint(user_bp, url_prefix="/api/user")
    app.register_blueprint(dataset_bp, url_prefix="/api/dataset")
    app.register_blueprint(query_bp, url_prefix="/api")

    @app.route("/")
    def index():
        return jsonify({
            "message": "单细胞 ANN 检索系统后端服务已启动",
            "module": "成员C：后端服务 + API接口",
            "apis": [
                "GET /api/health",
                "GET /api/dataset/info",
                "POST /api/search",
                "POST /api/user/register",
                "POST /api/user/login",
                "GET /api/user/list"
            ]
        })

    @app.route("/api/health")
    def health():
        return jsonify({
            "status": "ok",
            "message": "Flask 后端运行正常"
        })

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="127.0.0.1", port=5000, debug=True)