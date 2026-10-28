import asyncio
import struct
import pytest
from servo_lab.modbus_tcp import make_adu,parse_adu,handle_frame,serve_client,run_local_server
from servo_lab.plc_contract import VirtualRegisterImage,Register,StatusCode

def req(fc,body=b''):
    return make_adu(7,1,bytes([fc])+body)

def response_pdu(image,frame):
    tid,unit,pdu=parse_adu(handle_frame(image,frame))
    assert (tid,unit)==(7,1)
    return pdu

def test_read_holding_and_status():
    x=VirtualRegisterImage()
    x.write_holding(Register.SEQUENCE,123)
    assert response_pdu(x,req(3,struct.pack('>HH',1,1)))==b'\x03\x02\x00\x7b'
    x.set_telemetry(status=StatusCode.MOVING,fault=0,position_m=.02,speed_m_s=.4)
    assert response_pdu(x,req(4,struct.pack('>HH',100,2)))==b'\x04\x04\x00\x02\x00\x00'

def test_write_single_multi_and_exceptions():
    x=VirtualRegisterImage()
    write=struct.pack('>HH',1,55)
    assert response_pdu(x,req(6,write))==bytes([6])+write
    assert x.read_holding(1)==55
    values=struct.pack('>HH',18,19)
    data=struct.pack('>HHB',2,2,4)+values
    assert response_pdu(x,req(16,data))==bytes([16])+struct.pack('>HH',2,2)
    assert x.read_holding(2)==18 and x.read_holding(3)==19
    # Reject write crossing from writable address 3 to read-only 4 without any partial write.
    old=x.read_holding(3)
    data=struct.pack('>HHB',3,2,4)+values
    assert response_pdu(x,req(16,data))==b'\x90\x02'
    assert x.read_holding(3)==old
    assert response_pdu(x,req(7))==b'\x87\x01'

def test_invalid_mbap_rejected():
    frame=req(3,struct.pack('>HH',0,1))
    with pytest.raises(ValueError):parse_adu(frame[:-1])
    with pytest.raises(ValueError):parse_adu(frame[:2]+b'\x00\x01'+frame[4:])

def test_nonlocal_bind_refused():
    async def probe():
        with pytest.raises(ValueError):await run_local_server('0.0.0.0',15020)
    asyncio.run(probe())

def test_actual_local_tcp_exchange():
    async def exercise():
        x=VirtualRegisterImage()
        server=await asyncio.start_server(lambda r,w:serve_client(r,w,x),'127.0.0.1',0)
        host,port=server.sockets[0].getsockname()[:2]
        try:
            reader,writer=await asyncio.open_connection(host,port)
            frame=req(6,struct.pack('>HH',1,77))
            writer.write(frame);await writer.drain()
            recv=await asyncio.wait_for(reader.readexactly(len(frame)),timeout=1)
            assert recv==frame and x.read_holding(1)==77
            frame=req(3,struct.pack('>HH',1,1))
            writer.write(frame);await writer.drain()
            header=await asyncio.wait_for(reader.readexactly(7),timeout=1)
            length=struct.unpack('>H',header[4:6])[0]
            rest=await asyncio.wait_for(reader.readexactly(length-1),timeout=1)
            assert parse_adu(header+rest)[2]==b'\x03\x02\x00\x4d'
            writer.close();await writer.wait_closed()
        finally:
            server.close();await server.wait_closed()
    asyncio.run(exercise())


def test_fixed_seed_malformed_tcp_frames_never_partially_apply_writes():
    import random
    rng=random.Random(812)
    x=VirtualRegisterImage()
    baseline=x.read_holding(1)
    for _ in range(1200):
        frame=bytes(rng.randrange(256) for _ in range(rng.randrange(0,45)))
        try:handle_frame(x,frame)
        except (ValueError,struct.error):pass
    assert x.read_holding(1)==baseline
