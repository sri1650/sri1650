from tools.generate_dashboard import generate
from pathlib import Path


def test_dashboard_has_embedded_scenarios(tmp_path):
    p=generate(tmp_path/'dashboard.html')
    s=p.read_text()
    assert '<svg id="position"' in s
    assert '<svg id="current"' in s
    assert 'Software-in-the-loop' in s
    assert 'Encoder invalid' in s
    assert 'Heartbeat timeout' in s
    assert '__JSON_DATA__' not in s
    assert 'position_m' in s
