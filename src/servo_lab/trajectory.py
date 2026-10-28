"""Smooth rest-to-rest quintic trajectory with analytic velocity/acceleration/jerk bounds."""
from __future__ import annotations
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class TrajectoryPoint:
    position_m:float
    velocity_m_s:float
    acceleration_m_s2:float
    jerk_m_s3:float


@dataclass(frozen=True)
class QuinticMove:
    start_m:float
    end_m:float
    duration_s:float

    def __post_init__(self):
        if not (self.duration_s>0 and math.isfinite(self.duration_s)):
            raise ValueError("positive finite move duration required")

    @classmethod
    def for_limits(cls,start_m:float,end_m:float, *,v_max:float,a_max:float,j_max:float)->"QuinticMove":
        if min(v_max,a_max,j_max)<=0:
            raise ValueError("positive trajectory limits required")
        d=abs(end_m-start_m)
        t=max(0.1,1.875*d/v_max,math.sqrt((10*math.sqrt(3)/3)*d/a_max),(60*d/j_max)**(1/3))
        return cls(start_m,end_m,t)

    def sample(self,t:float)->TrajectoryPoint:
        if t<=0:
            return TrajectoryPoint(self.start_m,0,0,0)
        if t>=self.duration_s:
            return TrajectoryPoint(self.end_m,0,0,0)
        s=t/self.duration_s
        d=self.end_m-self.start_m
        T=self.duration_s
        f=10*s**3-15*s**4+6*s**5
        df=30*s**2-60*s**3+30*s**4
        ddf=60*s-180*s**2+120*s**3
        dddf=60-360*s+360*s**2
        return TrajectoryPoint(self.start_m+d*f,d*df/T,d*ddf/T**2,d*dddf/T**3)
