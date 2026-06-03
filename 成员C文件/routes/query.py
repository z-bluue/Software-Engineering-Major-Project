from flask import Blueprint, request, jsonify

from utils.search_service import search_by_cell_index, search_by_vector


query_bp = Blueprint("query", __name__)


@query_bp.route("/search", methods=["POST"])
def search():
    try:
        data = request.get_json(force=True)

        top_k = int(data.get("top_k", 10))
        metric = data.get("metric", "l2")

        filter_field = data.get("filter_field")
        filter_value = data.get("filter_value")

        if "cell_index" in data:
            cell_index = int(data["cell_index"])
            results = search_by_cell_index(
                cell_index=cell_index,
                top_k=top_k,
                metric=metric,
                filter_field=filter_field,
                filter_value=filter_value
            )

            return jsonify({
                "success": True,
                "query_type": "cell_index",
                "query_cell_index": cell_index,
                "top_k": top_k,
                "metric": metric,
                "filter": {
                    "field": filter_field,
                    "value": filter_value
                },
                "results": results
            })

        if "query_vector" in data:
            query_vector = data["query_vector"]
            results = search_by_vector(
                query_vector=query_vector,
                top_k=top_k,
                metric=metric,
                filter_field=filter_field,
                filter_value=filter_value
            )

            return jsonify({
                "success": True,
                "query_type": "query_vector",
                "top_k": top_k,
                "metric": metric,
                "filter": {
                    "field": filter_field,
                    "value": filter_value
                },
                "results": results
            })

        return jsonify({
            "success": False,
            "message": "请求中必须包含 cell_index 或 query_vector"
        }), 400

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500