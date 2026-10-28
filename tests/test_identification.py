import numpy as np
import pytest
from servo_lab.identification import (
    electrical_step_response,synthetic_locked_rotor_data,fit_locked_rotor_rl,
    fit_equivalent_mechanics,synthetic_mechanical_data
)

def test_exact_rl_initial_and_limit():
    t=np.array([0,0.05])
    y=electrical_step_response(t,12,2,.005)
    assert y[0]==0
    assert y[-1]==pytest.approx(6,abs=1e-3)

def test_synthetic_rl_fitted_on_heldout_samples():
    t,y=synthetic_locked_rotor_data(resistance_ohm=1.5,inductance_h=.003)
    fit=fit_locked_rotor_rl(t,y,8)
    assert fit.resistance_ohm==pytest.approx(1.5,rel=.015)
    assert fit.inductance_h==pytest.approx(.003,rel=.06)
    assert fit.holdout_rmse_a<.06
    assert fit.resistance_ci95_ohm[0]<fit.resistance_ohm<fit.resistance_ci95_ohm[1]

def test_bad_identification_input_rejected():
    t=np.arange(100)*.001
    with pytest.raises(ValueError):fit_locked_rotor_rl(t,np.zeros_like(t),8)
    with pytest.raises(ValueError):fit_locked_rotor_rl(t[::-1],np.linspace(0,2,len(t)),8)

def test_mechanical_fit_with_known_torque_constant():
    speed,acc,current=synthetic_mechanical_data(inertia_kg_m2=.004,friction_nm_s_rad=.00018,
        coulomb_nm=.012,torque_constant_nm_a=.16)
    fit=fit_equivalent_mechanics(speed,acc,current,.16)
    assert fit.equivalent_inertia_kg_m2==pytest.approx(.004,rel=.01)
    assert fit.viscous_friction_nm_s_rad==pytest.approx(.00018,abs=.00005)
    assert fit.smoothed_coulomb_torque_nm==pytest.approx(.012,abs=.0004)
    assert fit.residual_rmse_nm<.001

def test_mechanical_unidentifiable_input_rejected():
    with pytest.raises(ValueError):fit_equivalent_mechanics(np.ones(100),np.zeros(100),np.ones(100),.16)
