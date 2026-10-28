#!/usr/bin/env python3
"""Reproducible host-executed firmware/PLC/driver/motor digital-twin validation release."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import random
import statistics
import sys
import os

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
sys.path.insert(0,str(ROOT))
from servo_lab.virtual_bench import run_bench,save_trace,SCENARIOS,PublishedBench
from tools.build_virtual_firmware import build

OUT=ROOT/'outputs/virtual_bench'

def percentile(a:list[float],q:float)->float:
    s=sorted(a);pos=(len(s)-1)*q;i=int(pos);f=pos-i;return s[i]*(1-f)+s[min(i+1,len(s)-1)]*f

def chart(traces:dict):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    nominal=traces['nominal']
    t=[x['t_s'] for x in nominal]
    fig,ax=plt.subplots(figsize=(10,4))
    ax.plot(t,[x['position_deg'] for x in nominal],label='Simulated encoder position (deg)',linewidth=1.8)
    ax.plot(t,[x['target_deg'] for x in nominal],label='PLC requested position (deg)',linestyle='--',alpha=.6)
    ax.set(xlabel='Simulation time (s)',ylabel='Output angle (deg)',title='Vendor-informed rotary axis: C firmware + virtual motor + PLC')
    ax.grid(alpha=.25);ax.legend();fig.tight_layout();fig.savefig(OUT/'rotary_motion.png',dpi=150);plt.close(fig)
    fig,ax=plt.subplots(figsize=(10,4))
    ax.plot(t,[x['winding_current_a'] for x in nominal],label='Virtual motor winding current')
    ax.plot(t,[x['duty'] for x in nominal],label='Signed H-bridge duty')
    ax.set(xlabel='Simulation time (s)',ylabel='A / normalized duty',title='Assumed winding/current sensor and PWM dynamics')
    ax.grid(alpha=.25);ax.legend();fig.tight_layout();fig.savefig(OUT/'current_and_pwm.png',dpi=150);plt.close(fig)
    labels=[x for x in SCENARIOS if x not in ('nominal','command_stop','bad_target')]
    vals=[]
    for name in labels:
        r=traces[name];ff=next((i for i,row in enumerate(r) if row['state']=='FAULT'),None)
        vals.append(abs(r[-1]['position_deg']-r[ff]['position_deg']) if ff is not None else 0)
    fig,ax=plt.subplots(figsize=(10,4))
    ax.barh(labels,vals)
    ax.set(xlabel='Simulated extra angular travel after fault (deg)',title='High-impedance virtual coast: not a safe stopping distance')
    fig.tight_layout();fig.savefig(OUT/'fault_coasting.png',dpi=150);plt.close(fig)

def dashboard(traces:dict,summaries:dict):
    # Self-contained, offline replay of real generated traces; no network or live actuator control.
    data=json.dumps({name:{'trace':rows,'summary':summaries[name]} for name,rows in traces.items()},separators=(',',':'))
    html='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Virtual Servo Commissioning — Software Replay</title><style>
:root{color-scheme:dark}body{margin:0;background:#0d1320;color:#edf3fc;font:15px system-ui,Arial,sans-serif}.wrap{max-width:1150px;margin:auto;padding:24px}.overline{color:#70baff;font-weight:700;letter-spacing:.11em;font-size:12px}h1{margin:8px 0;font-size:clamp(24px,4vw,42px)}.alert{border:1px solid #d5a453;background:#34281a;color:#ffe5aa;padding:13px;border-radius:10px;margin:18px 0}.controls{display:flex;gap:16px;flex-wrap:wrap;align-items:center;margin-bottom:16px}select,input{accent-color:#73b6ff;border:1px solid #43536a;border-radius:9px;background:#162339;color:white;padding:8px}input[type=range]{flex:1;min-width:170px}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px}.card{background:#172236;border:1px solid #33445d;border-radius:12px;padding:16px}.label{font-size:12px;color:#8da5bf;margin-bottom:7px}.value{font-size:24px;font-weight:700}.plot{margin:16px 0;background:#141e30;border:1px solid #34435d;border-radius:12px;padding:12px}.plot canvas{display:block;width:100%;height:240px}.readout{display:flex;gap:18px;flex-wrap:wrap;font-variant-numeric:tabular-nums;color:#c3d5ed}.legend{font-size:12px;color:#b4c5da;margin-top:8px}.status{font-weight:700}.foot{color:#9fb5d0;font-size:13px;line-height:1.5;margin:20px 0}a{color:#85bdff}</style></head><body><div class="wrap">
<div class="overline">PROJECT 4 / VERIFIED SOFTWARE REPLAY</div><h1>Industrial Servo — Virtual Commissioning</h1>
<div class="alert"><strong>SIMULATED ONLY.</strong> Published motor ratings are combined with assumed inertia, friction, inductance, power electronics and sensor behavior. No STM32 board, motor, industrial safety circuit, physical PLC or actual CANopen fieldbus was tested. These controls replay stored evidence; they do not control hardware.</div>
<div class="controls"><label>Scenario <select id="scenario"></select></label><label>Frame <input id="frame" type="range" min="0" max="429" value="0"></label><button id="play" style="background:#2b74a8;color:white;border:0;padding:9px 16px;border-radius:8px;cursor:pointer">Play</button></div>
<div class="cards"><div class="card"><div class="label">Fault</div><div class="value" id="fault">NONE</div></div><div class="card"><div class="label">Firmware state</div><div class="value" id="state">READY</div></div><div class="card"><div class="label">Peak current (A)</div><div class="value" id="peak">—</div></div><div class="card"><div class="label">Final angle (°)</div><div class="value" id="final">—</div></div></div>
<div class="plot"><canvas id="position"></canvas><div class="legend">Blue: output angle | Pale dashed: operator target | Vertical cursor: selected sample</div></div>
<div class="plot"><canvas id="drive"></canvas><div class="legend">Yellow: normalized commanded duty | Green: winding current (A). Scales shown as numeric axis values.</div></div>
<div class="readout"><span id="t"></span><span id="angle"></span><span id="rpm"></span><span id="current"></span><span id="enabled"></span></div>
<div class="foot">Digital twin: same portable C firmware core used by the Cortex-M4 cross-compile test, plus the Pololu #4693-informed motor model, virtual #2992 driver, 3,200-count quadrature encoder and simulated rotary PLC. Software current limiting is not a physical current-limiting circuit. Prepared for engineering portfolio review only.</div></div>
<script>const DATA=__DATA__;const s=document.querySelector('#scenario'),slider=document.querySelector('#frame');let playing=null;Object.keys(DATA).forEach(name=>{const o=document.createElement('option');o.textContent=name.replaceAll('_',' ');o.value=name;s.appendChild(o)});
function draw(id,rows,series,range,idx){let canvas=document.getElementById(id),dpr=window.devicePixelRatio||1,rect=canvas.getBoundingClientRect();let w=canvas.width=Math.max(320,rect.width*dpr),h=canvas.height=240*dpr,ctx=canvas.getContext('2d');ctx.setTransform(1,0,0,1,0,0);ctx.clearRect(0,0,w,h);let l=55*dpr,r=12*dpr,t=20*dpr,b=30*dpr,W=w-l-r,H=h-t-b;ctx.strokeStyle='#435069';ctx.lineWidth=dpr;for(let n=0;n<=4;n++){let y=t+H*n/4;ctx.beginPath();ctx.moveTo(l,y);ctx.lineTo(w-r,y);ctx.stroke();ctx.fillStyle='#c1d5ed';ctx.font=12*dpr+'px sans-serif';ctx.fillText((range[1]-(range[1]-range[0])*n/4).toFixed(1),4*dpr,y+4*dpr)}
series.forEach(([key,color,dash])=>{ctx.strokeStyle=color;ctx.lineWidth=2*dpr;ctx.setLineDash(dash?[7*dpr,4*dpr]:[]);ctx.beginPath();rows.forEach((v,i)=>{let x=l+i/(rows.length-1)*W,y=t+(range[1]-v[key])/(range[1]-range[0])*H;if(i===0)ctx.moveTo(x,y);else ctx.lineTo(x,y)});ctx.stroke();ctx.setLineDash([])});let x=l+idx/(rows.length-1)*W;ctx.strokeStyle='#f2f5ff';ctx.beginPath();ctx.moveTo(x,t);ctx.lineTo(x,t+H);ctx.stroke();}
function render(){let p=DATA[s.value],rows=p.trace,i=Number(slider.value),r=rows[i];document.getElementById('fault').textContent=r.fault;document.getElementById('state').textContent=r.state;document.getElementById('peak').textContent=p.summary.max_abs_current_a.toFixed(3);document.getElementById('final').textContent=p.summary.final_angle_deg.toFixed(2);document.getElementById('t').textContent='t='+r.t_s.toFixed(2)+'s';document.getElementById('angle').textContent='angle='+r.position_deg.toFixed(2)+'°';document.getElementById('rpm').textContent='speed='+r.velocity_rpm.toFixed(2)+'rpm';document.getElementById('current').textContent='I='+r.winding_current_a.toFixed(3)+'A';document.getElementById('enabled').textContent='PWM='+r.enabled;draw('position',rows,[['position_deg','#78baff',false],['target_deg','#d5e6ff',true]],[-115,115],i);draw('drive',rows,[['duty','#f4c26c',false],['winding_current_a','#87dda4',false]],[-.8,.8],i);}
function changed(){let rows=DATA[s.value].trace;slider.max=rows.length-1;slider.value=0;render()};s.addEventListener('change',changed);slider.addEventListener('input',render);window.addEventListener('resize',render);document.querySelector('#play').addEventListener('click',()=>{if(playing){clearInterval(playing);playing=null;document.querySelector('#play').textContent='Play';return}document.querySelector('#play').textContent='Pause';playing=setInterval(()=>{let next=Number(slider.value)+1;if(next>Number(slider.max)){clearInterval(playing);playing=null;document.querySelector('#play').textContent='Play';return}slider.value=next;render()},25)});changed();</script></body></html>'''
    (OUT/'virtual_commissioning_dashboard.html').write_text(html.replace('__DATA__',data))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--samples',type=int,default=200);ap.add_argument('--seed',type=int,default=2026);args=ap.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    built=build(ROOT/'build/virtual_firmware',arm=True)
    runs={name:run_bench(name) for name in SCENARIOS}
    traces={name:result.trace for name,result in runs.items()}
    summary={name:result.summary() for name,result in runs.items()}
    for name in ('nominal','estop','encoder_loss','jam','undervoltage'):
        save_trace(traces[name],OUT/(name+'_trace.csv'))
    uncertainty=[];rand=random.Random(args.seed)
    for i in range(args.samples):
        mass=rand.uniform(.7,1.3);friction=rand.uniform(.7,1.3)
        r=run_bench('nominal',load_scale=mass,friction_scale=friction)
        accepted=(r.fault=='NONE' and r.final_state=='DONE' and abs(r.final_angle_deg)<2 and r.max_abs_current_a<0.75)
        uncertainty.append({'seed_index':i,'assumed_inertia_multiplier':mass,
                            'assumed_friction_multiplier':friction,
                            'finished':accepted,'final_deg':r.final_angle_deg,'peak_a':r.max_abs_current_a})
    with (OUT/'assumption_variation.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(uncertainty[0]));w.writeheader();w.writerows(uncertainty)
    nominal=runs['nominal'];faults=[runs[name] for name in SCENARIOS if runs[name].fault!='NONE']
    report={
      'scope':'HARDWARE-NEUTRAL_C_CORE_PLUS_VENDOR_INFORMED_VIRTUAL_BENCH__NO_PHYSICAL_TESTS',
      'software_validation_status':'PASS' if nominal.fault=='NONE' and nominal.final_state=='DONE' and
           all(x.post_fault_enabled_violations==0 for x in faults) and all(x.fault!='NONE' for x in faults) else 'FAIL',
      'source_config':'config/published_reference_bench.json',
      'firmware':built,'nominal':nominal.summary(),
      'fault_scenarios':{k:v for k,v in summary.items() if k!='nominal'},
      'inhibit_violations_all_faults':sum(x.post_fault_enabled_violations for x in faults),
      'fault_scenarios_with_latches':len(faults),
      'assumption_variation':{
        'seed':args.seed,'samples':args.samples,'uniform_inertia_multiplier':[.7,1.3],
        'uniform_friction_multiplier':[.7,1.3],
        'screen_passes':sum(x['finished'] for x in uncertainty),
        'final_position_abs_error_deg_p95':percentile([abs(x['final_deg']) for x in uncertainty],.95),
        'peak_current_a_p95':percentile([x['peak_a'] for x in uncertainty],.95),
        'not_a_reliability_probability':True,
      },
    }
    (OUT/'release_results.json').write_text(json.dumps(report,indent=2)+'\n')
    chart(traces);dashboard(traces,summary)
    spec=PublishedBench.load()
    report_md=f'''# Project 4 — Virtual Engineering Release (28 October 2026)

**Software digital twin: {report['software_validation_status']}. No physical motor, MCU, PLC or safety-related equipment was used.**

## Real manufacturer facts versus inferred and assumed inputs

- ST STM32G474RE, Cortex-M4 170 MHz with 512 KiB Flash and 128 KiB SRAM (manufacturer specification). ARM cross-compilation demonstrates code generation only; the ELF has **no functional vendor HAL or MCU GPIO/PWM/ADC/encoder configuration**, and is **not a flash-ready commissioned firmware image**.
- Pololu #4693, 24 V, 200 rpm unloaded output, 0.1 A no-load current, 3.0 A **extrapolated** stall current, 23 kg-cm extrapolated output torque, 50:1 gearing, 3,200 counts per output revolution (quadrature x4). Stall is not a continuous operating point.
- Pololu #2992, 6.5–40 V *absolute-max supply range* and 13 A published continuous-driver rating, default ~30 A chopping threshold. That default is **not suitable as a 3 A motor overcurrent protection**. CS ~40 mV/A + 50 mV offset is not available in all switching/braking states, so the simulated signed-current sensor is an **idealised replacement**.
- From vendor numbers, motor R≈{spec.R:.2f} Ω and K_e≈{spec.Ke:.5f} V/(rad/s), *inferred and approximate*. L={spec.L*1000:.1f} mH, gearbox η={spec.eta:.2f}, equivalent inertia J={spec.J:.5f} kg·m², friction/temperature model and 0.75 A operating limit are **assumptions**.

Sources: https://www.st.com/en/microcontrollers-microprocessors/stm32g474re.html · https://www.pololu.com/product/4693 · https://www.pololu.com/product/2992

## Actual virtual test results

| Metric | Software evidence |
|---|---:|
| C firmware in host simulation | Compiled, executed |
| Cortex-M4 freestanding binary | {'ARM ELF generated' if built['arm_compile_only'] else 'Unavailable'} (compile-only) |
| Nominal PLC command | 90° move, dwell, return to 0° |
| Nominal final angle | {nominal.final_angle_deg:.3f}° |
| Peak output speed | {nominal.peak_abs_output_speed_rpm:.3f} rpm |
| Peak simulated winding current | {nominal.max_abs_current_a:.3f} A |
| Nominal firmware state | {nominal.final_state} |
| Faults latched (defined scenarios) | {len(faults)} |
| Software voltage-enable violations after latch | {report['inhibit_violations_all_faults']} |
| Assumption-screen passes | {report['assumption_variation']['screen_passes']}/{args.samples} |
| Seeded screen p95 final absolute angle | {report['assumption_variation']['final_position_abs_error_deg_p95']:.3f}° |
| Seeded screen p95 peak motor current | {report['assumption_variation']['peak_current_a_p95']:.3f} A |

The seeded inertia/friction ranges are arbitrary ±30% mathematical scenarios—not measured manufacturing variation, statistical reliability or product qualification.

## What the virtual machine contains

1. **Published component targets** and assumption-provenance config.
2. **One C control/supervisor core** used by the host simulation and a Cortex-M4 cross-compiled artifact.
3. **A software motor/gearbox/load model** with idealised PWM H-bridge, ADC/encoder feedback, supply, winding heating and inertia.
4. **Rotary PLC register image and Modbus PDU coverage**, with signed millidegree telemetry, command sequences and two-move machine sequencing. Loopback-only simulation; not a real PLC.
5. **Fault injection and recovery interfaces**: no automatic re-enable after a latched fault, software command inhibit verified.
6. **Offline interactive dashboard** generated from actual simulation traces rather than mock charts.
7. **Regression tests, original C++/Python SIL, CI**, and reproducible study outputs.

## Limitations that cannot be solved by more assumptions

- No actual ADC calibration, PWM/gate-drive behavior, encoder polarity or switching-braking measurement.
- No reliable real current measurement under all H-bridge commutation/braking states; software current limit is **not hardware protection**.
- No physical independent protective interlock, emergency stop, safe torque-off, guarding or measured stopping distance.
- No STM32 hardware-specific HAL, oscillator/clock, peripherals, timer interrupts, jitter or WCET measurement.
- No motor bearing/gearbox wear, real thermal limits, actual torque constant or shaft-load test.
- No CANopen/EtherCAT certification, networked PLC, validated physical homing or commissioning.

**Completion statement:** PROJECT 4 IS COMPLETE **FOR THE DEFINED SOFTWARE-ONLY / VIRTUAL BENCH SCOPE**. It is intentionally not labelled a hardware-tested, certified servo drive or deployed automation cell.

## Reproduction

```bash
python -m pip install -e '.[test]'
python tools/build_virtual_firmware.py
PYTHONPATH=src python tools/build_virtual_bench_evidence.py --samples {args.samples} --seed {args.seed}
PYTHONPATH=src python -m pytest -q
python tools/quality_gate.py
```

Open `outputs/virtual_bench/virtual_commissioning_dashboard.html` in any browser (offline).
'''
    (OUT/'VIRTUAL_ENGINEERING_RELEASE.md').write_text(report_md)
    print(json.dumps({'status':report['software_validation_status'],'faults':len(faults),
        'nominal_final_deg':nominal.final_angle_deg,'screen_passes':report['assumption_variation']['screen_passes'],
        'samples':args.samples,'dashboard':str((OUT/'virtual_commissioning_dashboard.html').relative_to(ROOT))},indent=2))
    return 0 if report['software_validation_status']=='PASS' else 1

if __name__=='__main__':raise SystemExit(main())
