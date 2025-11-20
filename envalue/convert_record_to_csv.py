from __future__ import annotations

import csv
import json
from pathlib import Path

INPUT_PATH = Path("/Volumes/WD_work/semi_parser-output_test-record-1027-11.json")
OUTPUT_PATH = Path("record_evalue-1027-11.csv")


def convert_envalue_json2csv(INPUT_PATH,OUTPUT_PATH) -> None:
    with INPUT_PATH.open("r", encoding="utf-8") as infile:
        records = json.load(infile)

    fieldnames = [
        "file_name",
        "TP",
        "FP",
        "FN",
        "precision",
        "recall",
        "f1_score",
        "detail_type",
        "field_name",
        "incorrect_value",
        "judgment",
        "reason",
    ]

    total_tp = 0
    total_fp = 0
    total_fn = 0

    with OUTPUT_PATH.open("w", encoding="utf-8-sig", newline="") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()

        for record in records:
            metrics = record.get("metrics", {})
            details = record.get("verification_details") or [None]

            tp = metrics.get("TP")
            fp = metrics.get("FP")
            fn = metrics.get("FN")

            if isinstance(tp, (int, float)):
                total_tp += tp
            if isinstance(fp, (int, float)):
                total_fp += fp
            if isinstance(fn, (int, float)):
                total_fn += fn

            for detail in details:
                row = {
                    "file_name": record.get("file_name", ""),
                    "TP": tp if tp is not None else "",
                    "FP": fp if fp is not None else "",
                    "FN": fn if fn is not None else "",
                    "precision": metrics.get("precision", ""),
                    "recall": metrics.get("recall", ""),
                    "f1_score": metrics.get("f1_score", ""),
                    "detail_type": "",
                    "field_name": "",
                    "incorrect_value": "",
                    "judgment": "",
                    "reason": "",
                }

                if detail:
                    field_key = next(
                        (key for key in ("Incorrect_Field", "Missing_Field") if key in detail),
                        None,
                    )
                    if field_key:
                        row["detail_type"] = field_key
                        row["field_name"] = detail.get(field_key, "")
                    row["incorrect_value"] = detail.get("Incorrect_Value", "")
                    row["judgment"] = detail.get("Judgment", "")
                    row["reason"] = detail.get("Reason", "")

                writer.writerow(row)

        precision_denominator = total_tp + total_fp
        recall_denominator = total_tp + total_fn
        precision_value = total_tp / precision_denominator if precision_denominator else ""
        recall_value = total_tp / recall_denominator if recall_denominator else ""
        if precision_value != "" and recall_value != "":
            f1_value = (
                2 * precision_value * recall_value / (precision_value + recall_value)
                if (precision_value + recall_value)
                else ""
            )
        else:
            f1_value = ""

        writer.writerow(
            {
                "file_name": "TOTAL",
                "TP": total_tp,
                "FP": total_fp,
                "FN": total_fn,
                "precision": precision_value,
                "recall": recall_value,
                "f1_score": f1_value,
                "detail_type": "",
                "field_name": "",
                "incorrect_value": "",
                "judgment": "",
                "reason": "",
            }
        )


if __name__ == "__main__":
    convert_envalue_json2csv(INPUT_PATH,OUTPUT_PATH)
