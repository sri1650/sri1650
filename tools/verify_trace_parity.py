#!/usr/bin/env python3
"""Cross-check actual compiled C++ SIL output against Python model (not hardware validation)."""
from __future__ import annotations
import argparse
import csv
import json
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]


def read_csv(path:Path):
    with path.open(newline="",encoding="utf-8") as f:
        rows=list(csv.DictReader(f))
    return {k:np.array([float(x[k]) for x in rows]) for k in rows[0] if k!="mode"}


def compare(cpp:Path,python:Path)->dict:
    a,b=read_csv(cpp),read_csv(python)
    t=a["t_s"]
    if t.size < 20 or b["t_s"].size < t.size:
        raise ValueError("insufficient data")
    x_ref=np.interp(t,b["t_s"],b["position_m"])
    diff=(a["pos_m"]-x_ref)*1000
    result={"cpp_samples":len(t),"python_samples":len(b["t_s"]),
            "final_position_difference_mm":float(diff[-1]),
            "maximum_abs_position_difference_mm":float(max(abs(diff))),
            "mean_abs_position_difference_mm":float(abs(diff).mean()),
            "final_cpp_error_mm":float((a["ref_m"][-1]-a["pos_m"][-1])*1000),
            "pass":bool(max(abs(diff))<.05 and abs(diff[-1])<.005),
            "interpretation":"C++ fixed-step control/plant checked against Python counterpart; numerical integrators differ; neither is physical validation."}
    return result


def main():
    p=argparse.ArgumentParser();p.add_argument("--cpp",type=Path,default=ROOT/"outputs/cpp_sil_trace.csv");p.add_argument("--python",type=Path,default=ROOT/"outputs/nominal_axis_trace.csv");p.add_argument("--output",type=Path,default=ROOT/"outputs/cross_language_check.json")
    args=p.parse_args()
    result=compare(args.cpp,args.python)
    args.output.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
    return 0 if result["pass"] else 2

if __name__=="__main__":raise SystemExit(main())
