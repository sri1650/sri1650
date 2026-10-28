import pytest
from servo_lab.schedulability import PeriodicTask,response_time_analysis,nominal_task_set

def test_nominal_assumed_schedulability():
    results=response_time_analysis(nominal_task_set())
    assert results['all_schedulable']
    assert results['assumed_utilisation']<.1

def test_overload_not_schedulable():
    tasks=[PeriodicTask('f',1000,800,1000),PeriodicTask('g',1000,800,1000)]
    assert not response_time_analysis(tasks)['all_schedulable']

def test_duplicate_and_bad_task_rejected():
    with pytest.raises(ValueError):PeriodicTask('x',1000,1,2000)
    with pytest.raises(ValueError):response_time_analysis([PeriodicTask('a',1000,20,1000)]*2)
