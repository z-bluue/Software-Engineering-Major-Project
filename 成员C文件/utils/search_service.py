import numpy as np

from utils.data_loader import load_vectors, get_cell_metadata


def search_by_cell_index(cell_index, top_k=10, metric="l2", filter_field=None, filter_value=None):
    vectors = load_vectors()

    if cell_index < 0 or cell_index >= vectors.shape[0]:
        raise ValueError("cell_index 超出范围")

    query_vector = vectors[cell_index]
    return search_by_vector(
        query_vector=query_vector,
        top_k=top_k,
        metric=metric,
        exclude_index=cell_index,
        filter_field=filter_field,
        filter_value=filter_value
    )


def search_by_vector(query_vector, top_k=10, metric="l2", exclude_index=None, filter_field=None, filter_value=None):
    vectors = load_vectors()

    query_vector = np.array(query_vector, dtype="float32")

    if query_vector.ndim != 1:
        raise ValueError("query_vector 必须是一维数组")

    if query_vector.shape[0] != vectors.shape[1]:
        raise ValueError(f"query_vector 维度错误，应为 {vectors.shape[1]}")

    if metric == "cosine":
        scores = cosine_distance(vectors, query_vector)
    else:
        scores = l2_distance(vectors, query_vector)

    candidate_indices = np.arange(vectors.shape[0])

    if exclude_index is not None:
        mask = candidate_indices != exclude_index
        candidate_indices = candidate_indices[mask]
        scores = scores[mask]

    # 条件过滤：例如限定 cell_type
    if filter_field and filter_value:
        filtered_indices = []
        filtered_scores = []

        for idx, score in zip(candidate_indices, scores):
            meta = get_cell_metadata(int(idx))
            if str(meta.get(filter_field, "")) == str(filter_value):
                filtered_indices.append(idx)
                filtered_scores.append(score)

        candidate_indices = np.array(filtered_indices)
        scores = np.array(filtered_scores)

    if len(candidate_indices) == 0:
        return []

    top_k = min(int(top_k), len(candidate_indices))
    top_positions = np.argsort(scores)[:top_k]

    results = []
    for rank, pos in enumerate(top_positions, start=1):
        idx = int(candidate_indices[pos])
        distance = float(scores[pos])
        metadata = get_cell_metadata(idx)

        results.append({
            "rank": rank,
            "cell_index": idx,
            "distance": distance,
            "metadata": metadata
        })

    return results


def l2_distance(vectors, query_vector):
    diff = vectors - query_vector
    return np.sqrt(np.sum(diff * diff, axis=1))


def cosine_distance(vectors, query_vector):
    vectors_norm = vectors / (np.linalg.norm(vectors, axis=1, keepdims=True) + 1e-8)
    query_norm = query_vector / (np.linalg.norm(query_vector) + 1e-8)
    similarity = np.dot(vectors_norm, query_norm)
    return 1.0 - similarity