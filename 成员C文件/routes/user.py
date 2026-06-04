import os
import json
import hashlib
from flask import Blueprint, request, jsonify


user_bp = Blueprint("user", __name__)

USER_FILE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "models", "users.json")
)


def load_users():
    if not os.path.exists(USER_FILE):
        return []

    with open(USER_FILE, "r", encoding="utf-8") as f:
        content = f.read().strip()
        if not content:
            return []
        return json.loads(content)


def save_users(users):
    with open(USER_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)


def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


@user_bp.route("/register", methods=["POST"])
def register():
    try:
        data = request.get_json(force=True)

        username = data.get("username", "").strip()
        password = data.get("password", "").strip()
        role = data.get("role", "user").strip()

        if not username or not password:
            return jsonify({
                "success": False,
                "message": "用户名和密码不能为空"
            }), 400

        users = load_users()

        for user in users:
            if user["username"] == username:
                return jsonify({
                    "success": False,
                    "message": "用户名已存在"
                }), 400

        new_user = {
            "id": len(users) + 1,
            "username": username,
            "password_hash": hash_password(password),
            "role": role
        }

        users.append(new_user)
        save_users(users)

        return jsonify({
            "success": True,
            "message": "注册成功",
            "user": {
                "id": new_user["id"],
                "username": new_user["username"],
                "role": new_user["role"]
            }
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


@user_bp.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json(force=True)

        username = data.get("username", "").strip()
        password = data.get("password", "").strip()

        users = load_users()
        password_hash = hash_password(password)

        for user in users:
            if user["username"] == username and user["password_hash"] == password_hash:
                return jsonify({
                    "success": True,
                    "message": "登录成功",
                    "user": {
                        "id": user["id"],
                        "username": user["username"],
                        "role": user["role"]
                    }
                })

        return jsonify({
            "success": False,
            "message": "用户名或密码错误"
        }), 401

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


@user_bp.route("/list", methods=["GET"])
def list_users():
    try:
        users = load_users()

        safe_users = []
        for user in users:
            safe_users.append({
                "id": user["id"],
                "username": user["username"],
                "role": user["role"]
            })

        return jsonify({
            "success": True,
            "users": safe_users
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


@user_bp.route("/delete/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    try:
        users = load_users()
        new_users = [user for user in users if user["id"] != user_id]

        if len(new_users) == len(users):
            return jsonify({
                "success": False,
                "message": "用户不存在"
            }), 404

        save_users(new_users)

        return jsonify({
            "success": True,
            "message": "用户删除成功"
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500