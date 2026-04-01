from io import BytesIO
from typing import Any

import pandas as pd


def parse_uploaded_file(filename: str, file_bytes: bytes) -> dict[str, Any]:
    """
    Parse CSV or Excel file and return a preview payload.
    """
    lower_name = filename.lower()

    if lower_name.endswith(".csv"):
        df = pd.read_csv(BytesIO(file_bytes))
    elif lower_name.endswith(".xlsx") or lower_name.endswith(".xls"):
        df = pd.read_excel(BytesIO(file_bytes))
    else:
        raise ValueError("Unsupported file type. Please upload a CSV or Excel file.")

    # Clean column names a bit
    df.columns = [str(col).strip() for col in df.columns]

    # Replace NaN with None so JSON response is cleaner
    preview_df = df.head(10).where(pd.notnull(df), None)

    return {
        "filename": filename,
        "row_count": int(len(df)),
        "column_count": int(len(df.columns)),
        "columns": list(df.columns),
        "preview_rows": preview_df.to_dict(orient="records"),
    }