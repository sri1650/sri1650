"""Minimal LOCALHOST-only Modbus/TCP transport for the virtual register image.

Implemented function codes 03, 04, 06, 16. No authentication, TLS, device
certification, electrical safety or actual drive bus is provided. Never expose
this educational server to an untrusted network or real actuator.
"""
from __future__ import annotations
import argparse
import asyncio
import struct
from .plc_contract import VirtualRegisterImage


def make_adu(transaction_id:int,unit_id:int,pdu:bytes)->bytes:
    if not 0<=transaction_id<=65535 or not 0<=unit_id<=255 or not (1<=len(pdu)<=253):
        raise ValueError("invalid MBAP fields")
    return struct.pack('>HHHB',transaction_id,0,len(pdu)+1,unit_id)+pdu


def parse_adu(frame:bytes)->tuple[int,int,bytes]:
    if len(frame)<8 or len(frame)>260:
        raise ValueError("invalid TCP frame length")
    tid,protocol,length,unit=struct.unpack('>HHHB',frame[:7])
    if protocol!=0 or length<2 or length>254 or len(frame)!=length+6:
        raise ValueError("invalid MBAP frame")
    return tid,unit,frame[7:]


def respond_pdu(image:VirtualRegisterImage,pdu:bytes)->bytes:
    if not pdu:raise ValueError('empty PDU')
    fc=pdu[0]
    def err(code:int)->bytes:
        return bytes([fc|0x80,code])
    if fc in (3,4):
        if len(pdu)!=5:return err(3)
        start,count=struct.unpack('>HH',pdu[1:])
        if not 1<=count<=125:return err(3)
        try:
            vals=[image.read_holding(x) if fc==3 else image.read_input(x)
                  for x in range(start,start+count)]
        except (KeyError,ValueError):return err(2)
        return bytes([fc,count*2])+struct.pack('>'+str(count)+'H',*vals)
    if fc==6:
        if len(pdu)!=5:return err(3)
        address,value=struct.unpack('>HH',pdu[1:])
        try:image.write_holding(address,value)
        except (KeyError,ValueError):return err(2)
        return pdu
    if fc==16:
        if len(pdu)<6:return err(3)
        address,count,byte_count=struct.unpack('>HHB',pdu[1:6])
        if not 1<=count<=123 or byte_count!=count*2 or len(pdu)!=6+byte_count:
            return err(3)
        vals=struct.unpack('>'+str(count)+'H',pdu[6:])
        # Validate *all* addresses before any write to avoid partial updates.
        try:
            for addr in range(address,address+count):image.read_holding(addr)
        except KeyError:return err(2)
        for n,value in enumerate(vals):image.write_holding(address+n,value)
        return bytes([fc])+struct.pack('>HH',address,count)
    return err(1)


def handle_frame(image:VirtualRegisterImage,frame:bytes)->bytes:
    tid,unit,pdu=parse_adu(frame)
    return make_adu(tid,unit,respond_pdu(image,pdu))


async def serve_client(reader:asyncio.StreamReader,writer:asyncio.StreamWriter,image:VirtualRegisterImage):
    try:
        while True:
            try:header=await asyncio.wait_for(reader.readexactly(7),timeout=10)
            except (asyncio.TimeoutError,asyncio.IncompleteReadError):break
            _,protocol,length,_=struct.unpack('>HHHB',header)
            if protocol!=0 or not 2<=length<=254:break
            try:pdu=await asyncio.wait_for(reader.readexactly(length-1),timeout=5)
            except (asyncio.TimeoutError,asyncio.IncompleteReadError):break
            try:response=handle_frame(image,header+pdu)
            except ValueError:break
            writer.write(response)
            await writer.drain()
    finally:
        writer.close()
        await writer.wait_closed()


async def run_local_server(host:str='127.0.0.1',port:int=15020):
    if host not in ('127.0.0.1','::1','localhost'):
        raise ValueError('refusing non-loopback bind for educational test server')
    image=VirtualRegisterImage()
    server=await asyncio.start_server(lambda r,w:serve_client(r,w,image),host,port)
    async with server:await server.serve_forever()


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--host',default='127.0.0.1')
    p.add_argument('--port',type=int,default=15020)
    args=p.parse_args()
    asyncio.run(run_local_server(args.host,args.port))

if __name__=='__main__':main()
