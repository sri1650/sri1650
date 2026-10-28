#!/usr/bin/env python3
"""One-command deterministic pre-Codex verification; outputs JSON evidence."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]


def run(name,cmd,timeout=120,stdout_file=None):
    start=time.perf_counter()
    proc=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,timeout=timeout,env={**os.environ,"PYTHONPATH":str(ROOT/"src")+os.pathsep+str(ROOT),
        "OPENBLAS_NUM_THREADS":"1","OMP_NUM_THREADS":"1","MPLBACKEND":"Agg"})
    if stdout_file and proc.returncode==0:
        Path(stdout_file).write_text(proc.stdout,encoding="utf-8")
    return {"name":name,"status":"pass" if proc.returncode==0 else "fail",
            "returncode":proc.returncode,"duration_s":round(time.perf_counter()-start,3),
            "stdout_tail":proc.stdout[-1500:] if not stdout_file else "saved to "+str(stdout_file),
            "stderr_tail":proc.stderr[-900:]}


def main():
    ap=argparse.ArgumentParser();ap.add_argument("--output",type=Path,default=ROOT/"outputs/quality_gate.json");args=ap.parse_args()
    build=ROOT/"build/cpp"
    results=[]
    steps=[
      ("python_tests",[sys.executable,"-m","pytest","-q"],120,None),
      ("python_compile",[sys.executable,"-m","compileall","-q","src","tests","tools"],40,None),
      ("generate_cpp_config",[sys.executable,"tools/generate_cpp_config.py"],20,None),
      ("cmake_configure",["cmake","-S","cpp","-B",str(build),"-DCMAKE_BUILD_TYPE=Release"],60,None),
      ("cmake_build",["cmake","--build",str(build),"--parallel","4"],90,None),
      ("cpp_ctest",["ctest","--test-dir",str(build),"--output-on-failure"],40,None),
      ("cpp_sil_demo",[str(build/"servo_demo")],40,ROOT/"outputs/cpp_sil_trace.csv"),
      ("python_evidence",[sys.executable,"tools/build_evidence.py","--samples","100","--seed","2026"],90,None),
      ("cross_language_parity",[sys.executable,"tools/verify_trace_parity.py"],30,None),
      ("offline_dashboard",[sys.executable,"tools/generate_dashboard.py"],30,None),
      ("host_loop_benchmark",[str(build/"servo_host_cycle_benchmark")],30,ROOT/"outputs/host_loop_benchmark.json"),
      ("extended_hardware_neutral_evidence",[sys.executable,"tools/extended_prework.py","--host-benchmark",str(build/"servo_host_cycle_benchmark")],100,None),
    ]
    for name,cmd,timeout,out in steps:
        result=run(name,cmd,timeout,out)
        results.append(result)
        print(f"{name}: {result['status']} ({result['duration_s']}s)",flush=True)
        if result["status"]!="pass":break
    for x in results:
        x["stdout_tail"]=x["stdout_tail"].replace(str(ROOT),"<PROJECT_ROOT>")
        x["stderr_tail"]=x["stderr_tail"].replace(str(ROOT),"<PROJECT_ROOT>")
    report={"validation_scope":"Python/C++ SIL, virtual fieldbus, synthetic identification and host timing only — no physical/RTOS/hardware validation",
            "status":"PASS" if len(results)==len(steps) and all(x["status"]=="pass" for x in results) else "FAIL",
            "checks":results}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+"\n")
    print(report["status"])
    return 0 if report["status"]=="PASS" else 2

if __name__=="__main__":raise SystemExit(main())
