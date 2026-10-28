#include "bench_core.h"
#include <assert.h>
#include <math.h>
#include <stddef.h>

static BenchInput normal(uint32_t ms) {
    BenchInput x = {0};
    x.time_ms=ms; x.sample_ms=ms; x.encoder_good=1; x.driver_good=1;
    x.interlock_good=1; x.heartbeat_good=1;
    x.bus_voltage_v=24.0f; x.temperature_c=25.0f;
    return x;
}
int main(void){
    BenchCore core;BenchOutput out;
    bench_init(&core);
    BenchInput x=normal(0);
    bench_cycle(&core,&x,&out);
    assert(out.drive_enable==0 && out.state==BENCH_READY);
    x=normal(1);x.command=BENCH_CMD_MOVE;x.command_sequence=1;x.target_count=800;
    bench_cycle(&core,&x,&out);
    assert(out.drive_enable==1 && out.state==BENCH_MOVING);
    x=normal(2);x.estop=1;bench_cycle(&core,&x,&out);
    assert(out.drive_enable==0 && out.fault==BENCH_FAULT_ESTOP);
    x=normal(3);bench_cycle(&core,&x,&out);
    assert(out.drive_enable==0 && out.state==BENCH_FAULT);
    x=normal(4);x.command=BENCH_CMD_MOVE;x.command_sequence=2;
    bench_cycle(&core,&x,&out);
    assert(out.drive_enable==0);
    x=normal(5);x.command=BENCH_CMD_RESET;x.command_sequence=3;
    bench_cycle(&core,&x,&out);
    assert(out.drive_enable==0 && out.state==BENCH_READY && out.fault==0);
    x=normal(6);x.command=BENCH_CMD_MOVE;x.command_sequence=4;x.target_count=9999;
    bench_cycle(&core,&x,&out);
    assert(out.drive_enable==0 && out.fault==BENCH_FAULT_BAD_TARGET);
    bench_init(&core);
    x=normal(0);bench_cycle(&core,&x,&out);
    x=normal(1);x.winding_current_a=NAN;bench_cycle(&core,&x,&out);
    assert(out.fault==BENCH_FAULT_NUMERIC && out.drive_enable==0);
    return 0;
}
