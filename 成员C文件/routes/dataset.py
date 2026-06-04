from flask import Blueprint, jsonify

from utils.data_loader import get_dataset_info, get_column_values


dataset_bp = Blueprint("dataset", __name__)


@dataset_bp.route("/info", methods=["GET"])
def dataset_info():
    try:
        info = get_dataset_info()
        return jsonify({
            "success": True,
            "data": info
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


@dataset_bp.route("/status", methods=["GET"])
def dataset_status():
    try:
        info = get_dataset_info()
        return jsonify({
            "success": True,
            "status": "loaded",
            "cell_count": info["cell_count"],
            "vector_dim": info["vector_dim"],
            "message": "数据集已加载，后端可执行 Top-K 检索"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "status": "error",
            "message": str(e)
        }), 500
@dataset_bp.route("/column/<column_name>/values", methods=["GET"])
def dataset_column_values(column_name):
    try:
        values = get_column_values(column_name)

        return jsonify({
            "success": True,
            "column": column_name,
            "values": values,
            "count": len(values)
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500