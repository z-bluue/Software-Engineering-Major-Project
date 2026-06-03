import os
import numpy as np
import pandas as pd


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_DIR = os.path.join(BASE_DIR, "成员B文件", "data")

VECTOR_PATH = os.path.join(DATA_DIR, "cell_vectors.npy")
METADATA_PATH = os.path.join(DATA_DIR, "cell_metadata.csv")
COORD_PATH = os.path.join(DATA_DIR, "cell_2d_coords.csv")


_vectors_cache = None
_metadata_cache = None
_coords_cache = None


def load_vectors():
    global _vectors_cache

    if _vectors_cache is None:
        if not os.path.exists(VECTOR_PATH):
            raise FileNotFoundError(f"向量文件不存在: {VECTOR_PATH}")

        vectors = np.load(VECTOR_PATH)
        vectors = vectors.astype("float32")

        _vectors_cache = vectors

    return _vectors_cache


def load_metadata():
    global _metadata_cache

    if _metadata_cache is None:
        if not os.path.exists(METADATA_PATH):
            raise FileNotFoundError(f"元数据文件不存在: {METADATA_PATH}")

        metadata = pd.read_csv(METADATA_PATH)
        _metadata_cache = metadata

    return _metadata_cache


def load_coords():
    global _coords_cache

    if _coords_cache is None:
        if os.path.exists(COORD_PATH):
            _coords_cache = pd.read_csv(COORD_PATH)
        else:
            _coords_cache = None

    return _coords_cache


def get_dataset_info():
    vectors = load_vectors()
    metadata = load_metadata()
    coords = load_coords()

    return {
        "dataset_name": "liver processed dataset",
        "vector_file": "cell_vectors.npy",
        "metadata_file": "cell_metadata.csv",
        "cell_count": int(vectors.shape[0]),
        "vector_dim": int(vectors.shape[1]) if len(vectors.shape) > 1 else 0,
        "metadata_rows": int(metadata.shape[0]),
        "metadata_columns": list(metadata.columns),
        "has_2d_coords": coords is not None,
        "coord_rows": int(coords.shape[0]) if coords is not None else 0
    }


def get_cell_metadata(index):
    metadata = load_metadata()

    if index < 0 or index >= len(metadata):
        return {}

    row = metadata.iloc[index].to_dict()

    clean_row = {}
    for key, value in row.items():
        if pd.isna(value):
            clean_row[key] = None
        else:
            clean_row[key] = str(value)

    return clean_row
def get_column_values(column_name, limit=100):
    metadata = load_metadata()

    if column_name not in metadata.columns:
        raise ValueError(f"字段不存在: {column_name}")

    values = metadata[column_name].dropna().astype(str).unique().tolist()
    values = sorted(values)

    return values[:limit]