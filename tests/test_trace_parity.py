from pathlib import Path
from tools.verify_trace_parity import compare


def test_cpp_python_agree_on_retained_trace():
    root=Path(__file__).resolve().parents[1]
    r=compare(root/"outputs/cpp_sil_trace.csv",root/"outputs/nominal_axis_trace.csv")
    assert r["pass"]
    assert r["maximum_abs_position_difference_mm"]<.05
