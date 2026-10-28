#!/usr/bin/env python3
"""Strict SIL-only acceptance gate: prevents promotion of incomplete/error evidence."""
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/virtual_bench'

def verify():
    r=json.loads((OUT/'release_results.json').read_text())
    assert r['scope'].endswith('NO_PHYSICAL_TESTS')
    assert r['software_validation_status']=='PASS'
    assert r['nominal']['fault']=='NONE' and r['nominal']['final_state']=='DONE'
    assert abs(r['nominal']['final_angle_deg'])<2
    assert r['nominal']['max_abs_current_a']<0.75
    assert r['fault_scenarios_with_latches']>=12
    assert r['inhibit_violations_all_faults']==0
    assert all(x['post_fault_enabled_violations']==0 for x in r['fault_scenarios'].values())
    assert r['assumption_variation']['samples']==200
    assert r['assumption_variation']['not_a_reliability_probability']
    assert r['assumption_variation']['screen_passes']==200
    assert (OUT/'nominal_trace.csv').stat().st_size>1000
    assert (OUT/'rotary_motion.png').stat().st_size>1000
    assert (OUT/'fault_coasting.png').stat().st_size>1000
    page=(OUT/'virtual_commissioning_dashboard.html').read_text()
    assert 'SIMULATED ONLY' in page and '<canvas' in page and 'encoder_loss' in page
    assert 'No STM32 board' in page
    assert (OUT/'VIRTUAL_ENGINEERING_RELEASE.md').stat().st_size>2000
    assert (ROOT/'firmware/src/bench_core.c').exists()
    assert (ROOT/'build/virtual_firmware/libbench_core.so').exists() or (ROOT/'build/virtual_firmware/libbench_core.dylib').exists()
    print('PASS: virtual release evidence consistent, source-linked, physically unvalidated')

if __name__=='__main__':verify()
