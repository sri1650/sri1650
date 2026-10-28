"""Evidence-grade *synthetic* electrical/mechanical motor identification.

These routines need real measurements and an uncertainty model before they can be used
for motor commissioning. The example data are generated from assumed parameters.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import csv
import math
import numpy as np


@dataclass(frozen=True)
class ElectricalFit:
    resistance_ohm: float
    inductance_h: float
    train_rmse_a: float
    holdout_rmse_a: float
    resistance_ci95_ohm: tuple[float, float]
    inductance_ci95_h: tuple[float, float]
    voltage_v: float
    samples: int


def electrical_step_response(time_s: np.ndarray, voltage_v: float, resistance_ohm: float, inductance_h: float) -> np.ndarray:
    """Locked-rotor RL step; assumes zero initial current and zero back-EMF."""
    t=np.asarray(time_s,dtype=float)
    if voltage_v<=0 or resistance_ohm<=0 or inductance_h<=0 or not np.all(np.isfinite(t)) or np.any(t<0):
        raise ValueError("invalid RL step parameters")
    return (voltage_v/resistance_ohm)*(-np.expm1(-resistance_ohm*t/inductance_h))


def synthetic_locked_rotor_data(*, resistance_ohm: float, inductance_h: float,
                                voltage_v: float=8.0, samples: int=240,
                                dt_s: float=0.0001, noise_std_a: float=0.025,
                                seed: int=11) -> tuple[np.ndarray,np.ndarray]:
    if samples < 20 or dt_s<=0 or noise_std_a<0:
        raise ValueError("invalid experiment sampling")
    t=np.arange(samples,dtype=float)*dt_s
    y=electrical_step_response(t,voltage_v,resistance_ohm,inductance_h)
    y=y+np.random.default_rng(seed).normal(0,noise_std_a,samples)
    return t,y


def fit_locked_rotor_rl(time_s: np.ndarray, current_a: np.ndarray, voltage_v: float) -> ElectricalFit:
    """Constrained nonlinear least squares, deterministic 80/20 time split.

    Confidence intervals are approximate Gaussian residual intervals; they do NOT
    include systematic error, sensor calibration, heating or model discrepancy.
    """
    try:
        from scipy.optimize import least_squares
    except ImportError as exc:
        raise RuntimeError("Install optional analysis dependency: pip install -e '.[analysis]'") from exc
    t=np.asarray(time_s,dtype=float).reshape(-1)
    y=np.asarray(current_a,dtype=float).reshape(-1)
    if (len(t)<30 or y.shape!=t.shape or not np.all(np.isfinite(t)) or not np.all(np.isfinite(y))
        or np.any(np.diff(t)<=0) or t[0]<0 or not (voltage_v>0 and math.isfinite(voltage_v))):
        raise ValueError("need >=30 finite, strictly increasing sample times and positive constant step")
    if np.ptp(y)<0.1 or (t[-1]-t[0])<0.002:
        raise ValueError("insufficient excitation or observation window")
    cut=int(len(t)*0.8)
    # Use physically interpretable log-parameterisation to maintain positivity.
    steady=max(float(np.median(y[max(3,cut-10):cut])),0.01)
    r0=min(max(voltage_v/steady,0.05),100.0)
    # Choose a small, plausible time constant; least squares determines the final value.
    l0=r0*0.003
    def predict(z,t):
        return electrical_step_response(t,voltage_v,float(np.exp(z[0])),float(np.exp(z[1])))
    out=least_squares(lambda z:predict(z,t[:cut])-y[:cut],
        np.log([r0,l0]),bounds=(np.log([0.01,1e-6]),np.log([1000,1])),max_nfev=250,
        ftol=1e-12,xtol=1e-12,gtol=1e-12)
    if not out.success:
        raise RuntimeError("RL identification did not converge")
    residual=predict(out.x,t[:cut])-y[:cut]
    holdout=predict(out.x,t[cut:])-y[cut:]
    # Covariance in log-parameters, then first-order transform to R,L units.
    dof=max(1,cut-2)
    cov_log=np.linalg.pinv(out.jac.T@out.jac)*(float(residual@residual)/dof)
    est=np.exp(out.x)
    std=est*np.sqrt(np.maximum(0,np.diag(cov_log)))
    intervals=[(float(max(0,e-1.96*s)),float(e+1.96*s)) for e,s in zip(est,std)]
    return ElectricalFit(float(est[0]),float(est[1]),
        float(np.sqrt(np.mean(residual*residual))),float(np.sqrt(np.mean(holdout*holdout))),
        intervals[0],intervals[1],float(voltage_v),len(t))


@dataclass(frozen=True)
class InertiaFit:
    equivalent_inertia_kg_m2: float
    viscous_friction_nm_s_rad: float
    smoothed_coulomb_torque_nm: float
    residual_rmse_nm: float
    design_condition_number: float
    samples: int


def fit_equivalent_mechanics(speed_rad_s: np.ndarray, acceleration_rad_s2: np.ndarray,
                             current_a: np.ndarray, torque_constant_nm_a: float,
                             *, smoothing_speed_rad_s: float=0.5) -> InertiaFit:
    """Fit J*acc+b*omega+Tc*tanh(omega/vs)=Kt*i with *known* Kt.

    No unmeasured external load torque is included. Kt and J are not separately
    identifiable from these observations without at least one known quantity.
    """
    w=np.asarray(speed_rad_s,dtype=float).reshape(-1)
    a=np.asarray(acceleration_rad_s2,dtype=float).reshape(-1)
    i=np.asarray(current_a,dtype=float).reshape(-1)
    if (len(w)<40 or len(a)!=len(w) or len(i)!=len(w) or smoothing_speed_rad_s<=0 or
        torque_constant_nm_a<=0 or not all(np.all(np.isfinite(v)) for v in (w,a,i))):
        raise ValueError("invalid mechanical identification signals")
    X=np.column_stack((a,w,np.tanh(w/smoothing_speed_rad_s)))
    # Normalize columns before checking conditioning; quantities have different units.
    norms=np.linalg.norm(X,axis=0)
    if np.any(norms<1e-9):
        raise ValueError("mechanical parameters not identifiable: insufficient excitation")
    cond=float(np.linalg.cond(X/norms))
    if cond>150:
        raise ValueError("mechanical parameters not identifiable: correlated measurements")
    target=torque_constant_nm_a*i
    result,residuals,rank,_=np.linalg.lstsq(X,target,rcond=None)
    if rank!=3 or np.any(result<0):
        raise ValueError("invalid/physically inconsistent mechanical parameter estimate")
    err=X@result-target
    return InertiaFit(float(result[0]),float(result[1]),float(result[2]),
                      float(np.sqrt(np.mean(err*err))),cond,len(w))


def synthetic_mechanical_data(*, inertia_kg_m2: float, friction_nm_s_rad: float,
                              coulomb_nm: float, torque_constant_nm_a: float,
                              samples: int=1000, seed: int=14):
    if min(inertia_kg_m2,friction_nm_s_rad,coulomb_nm,torque_constant_nm_a)<=0:
        raise ValueError("positive synthetic parameters required")
    t=np.arange(samples,dtype=float)*0.001
    speed=12*np.sin(2*np.pi*1.2*t)+5*np.sin(2*np.pi*3.7*t)
    accel=12*(2*np.pi*1.2)*np.cos(2*np.pi*1.2*t)+5*(2*np.pi*3.7)*np.cos(2*np.pi*3.7*t)
    torque=inertia_kg_m2*accel+friction_nm_s_rad*speed+coulomb_nm*np.tanh(speed/0.5)
    current=torque/torque_constant_nm_a+np.random.default_rng(seed).normal(0,0.001,samples)
    return speed,accel,current


def save_electrical_observations(path: Path,time_s:np.ndarray,current_a:np.ndarray,voltage_v:float)->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",newline="",encoding="utf-8") as fh:
        w=csv.writer(fh);w.writerow(["time_s","current_a","applied_voltage_v"])
        for t,i in zip(time_s,current_a):w.writerow([format(float(t),".10g"),format(float(i),".10g"),voltage_v])
