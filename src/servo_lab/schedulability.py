"""Deterministic fixed-priority response-time analysis for hypothesised WCETs.

Not a measurement of Linux, FreeRTOS, ISR latency, peripheral timing or a certified
worst-case execution bound. Assumes independent preemptible periodic tasks.
"""
from __future__ import annotations
from dataclasses import dataclass
from math import ceil

@dataclass(frozen=True)
class PeriodicTask:
    name: str
    period_us: int
    wcet_us: int
    deadline_us: int

    def __post_init__(self):
        if not self.name or min(self.period_us,self.wcet_us,self.deadline_us)<=0 or self.deadline_us>self.period_us:
            raise ValueError("invalid periodic task")

@dataclass(frozen=True)
class TaskResponse:
    name:str
    response_time_us:int
    deadline_us:int
    schedulable:bool


def response_time_analysis(tasks:list[PeriodicTask])->dict:
    """Rate-monotonic priority; smaller period first, name breaks ties."""
    order=sorted(tasks,key=lambda t:(t.period_us,t.name))
    if len({t.name for t in order})!=len(order):raise ValueError("duplicate task")
    results=[]
    for i,task in enumerate(order):
        r=task.wcet_us
        for _ in range(200):
            nxt=task.wcet_us+sum(ceil(r/other.period_us)*other.wcet_us for other in order[:i])
            if nxt==r:break
            if nxt>task.deadline_us:
                r=nxt;break
            r=nxt
        results.append(TaskResponse(task.name,r,task.deadline_us,r<=task.deadline_us))
    util=sum(t.wcet_us/t.period_us for t in order)
    return {
      "assumed_utilisation":util,
      "all_schedulable":all(x.schedulable for x in results),
      "tasks":[vars(x) for x in results],
      "assumptions":"fixed-priority preemptive periodic scheduling; WCETs are assumptions, not measured hardware bounds",
    }


def nominal_task_set()->list[PeriodicTask]:
    return [
      PeriodicTask("current_control",1000,35,1000),
      PeriodicTask("velocity_control",4000,60,4000),
      PeriodicTask("position_control",10000,85,10000),
      PeriodicTask("communication_housekeeping",10000,120,10000),
    ]
