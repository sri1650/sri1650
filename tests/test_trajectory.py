import math
import pytest
from servo_lab.trajectory import QuinticMove


def test_quintic_endpoints_and_velocities():
    m=QuinticMove.for_limits(0,.1,v_max=.35,a_max=1,j_max=8)
    assert m.sample(0).position_m==0
    assert m.sample(m.duration_s).position_m==pytest.approx(.1)
    assert m.sample(.5*m.duration_s).position_m==pytest.approx(.05)
    assert m.sample(0).velocity_m_s==0
    assert m.sample(m.duration_s).velocity_m_s==0


def test_profile_respects_velocity_accel_jerk_caps():
    m=QuinticMove.for_limits(.04,.14,v_max=.35,a_max=1,j_max=8)
    x=[m.sample(k*m.duration_s/5000) for k in range(5001)]
    assert max(abs(y.velocity_m_s) for y in x)<.35001
    assert max(abs(y.acceleration_m_s2) for y in x)<1.00001
    assert max(abs(y.jerk_m_s3) for y in x)<=8.00001
    assert all(x[k+1].position_m>=x[k].position_m for k in range(len(x)-1))


def test_reverse_motion():
    m=QuinticMove.for_limits(.2,.05,v_max=.35,a_max=1,j_max=8)
    assert m.sample(m.duration_s/2).position_m==pytest.approx(.125)
    assert m.sample(.1*m.duration_s).velocity_m_s<0


def test_invalid_duration_rejected():
    with pytest.raises(ValueError):QuinticMove(0,.1,0)
    with pytest.raises(ValueError):QuinticMove.for_limits(0,.1,v_max=0,a_max=1,j_max=2)


def test_zero_distance_stays_still():
    m=QuinticMove.for_limits(.1,.1,v_max=.35,a_max=1,j_max=8)
    assert m.sample(.05).position_m==.1
    assert m.sample(.05).velocity_m_s==0
