"""Utilities for converting an Excel file of categories into JSONL documents."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable, List, Dict, Any, Optional

import pandas as pd


def load_categories(
    excel_path: Path,
    sheet_name: Optional[str],
    category_column: str,
    definition_column: str,
    metadata_columns: Iterable[str],
) -> List[Dict[str, Any]]:
    """Load category data from an Excel file.

    Args:
        excel_path: Path to the Excel workbook.
        sheet_name: Optional sheet name. If omitted the first sheet is used.
        category_column: Column containing the category name.
        definition_column: Column containing the category definition/description.
        metadata_columns: Additional columns to include in the document.

    Returns:
        A list of dictionaries representing category documents.
    """
    df = pd.read_excel(excel_path, sheet_name=sheet_name)
    missing_cols = {
        col
        for col in [category_column, definition_column, *metadata_columns]
        if col not in df.columns
    }
    if missing_cols:
        available = ", ".join(sorted(df.columns))
        missing = ", ".join(sorted(missing_cols))
        raise ValueError(
            f"Column(s) {missing} were not found in the workbook. "
            f"Available columns: {available}"
        )

    df = df.dropna(subset=[category_column, definition_column]).reset_index(drop=True)

    documents: List[Dict[str, Any]] = []
    for idx, row in df.iterrows():
        document: Dict[str, Any] = {
            "id": str(idx + 1),
            "category": str(row[category_column]).strip(),
            "definition": str(row[definition_column]).strip(),
        }
        for column in metadata_columns:
            document[column] = row[column]
        documents.append(document)
    return documents


def dump_jsonl(documents: Iterable[Dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fp:
        for doc in documents:
            fp.write(json.dumps(doc, ensure_ascii=False) + "\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Extract category documents from an Excel workbook and "
            "write them as newline-delimited JSON (JSONL)."
        )
    )
    parser.add_argument("excel_path", type=Path, help="Path to the Excel workbook")
    parser.add_argument(
        "--sheet-name",
        type=str,
        default=None,
        help="Optional Excel sheet name. Defaults to the first sheet.",
    )
    parser.add_argument(
        "--category-column",
        required=True,
        help="Column containing the category label.",
    )
    parser.add_argument(
        "--definition-column",
        required=True,
        help="Column containing the category definition or description.",
    )
    parser.add_argument(
        "--metadata-columns",
        nargs="*",
        default=(),
        help="Additional columns to include in the JSONL output.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("categories.jsonl"),
        help="Path to the JSONL output file.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    documents = load_categories(
        excel_path=args.excel_path,
        sheet_name=args.sheet_name,
        category_column=args.category_column,
        definition_column=args.definition_column,
        metadata_columns=args.metadata_columns,
    )
    dump_jsonl(documents, args.output)
    print(f"Wrote {len(documents)} documents to {args.output}")


if __name__ == "__main__":
    main()
