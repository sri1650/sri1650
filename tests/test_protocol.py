import pytest
from servo_lab.protocol import VirtualCommand,CommandReceiver,encode_command,decode_command


def test_virtual_transport_round_trip():
    cmd=VirtualCommand(10,"MOVE",.1)
    assert decode_command(encode_command(cmd))==cmd


def test_corruption_detected():
    frame=bytearray(encode_command(VirtualCommand(1,"MOVE",.1)))
    frame[6]^=1
    with pytest.raises(ValueError):decode_command(bytes(frame))


def test_duplicate_is_idempotent_but_conflicting_replay_rejected():
    rx=CommandReceiver()
    f=encode_command(VirtualCommand(4,"MOVE",.1))
    assert rx.accept(f)[0] is True
    assert rx.accept(f)[0] is False
    with pytest.raises(ValueError):rx.accept(encode_command(VirtualCommand(4,"MOVE",.2)))
    with pytest.raises(ValueError):rx.accept(encode_command(VirtualCommand(3,"STOP")))


def test_invalid_operation_rejected():
    with pytest.raises(ValueError):encode_command(VirtualCommand(0,"RUN_MOTOR",0))
    with pytest.raises(ValueError):decode_command(b"x")
