#ifndef BENCH_CORE_H
#define BENCH_CORE_H
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
/* Host and Cortex-M4 compile from this same portable source; no vendor GPIO or actual safety chain. */
enum { BENCH_BOOT=0, BENCH_READY=1, BENCH_MOVING=2, BENCH_DONE=3, BENCH_FAULT=4 };
enum { BENCH_CMD_NONE=0, BENCH_CMD_MOVE=1, BENCH_CMD_STOP=2, BENCH_CMD_RESET=3 };
enum {
  BENCH_FAULT_NONE=0, BENCH_FAULT_ESTOP=1, BENCH_FAULT_INTERLOCK=2,
  BENCH_FAULT_ENCODER=3, BENCH_FAULT_DRIVE=4, BENCH_FAULT_HEARTBEAT=5,
  BENCH_FAULT_BUS=6, BENCH_FAULT_TEMP=7, BENCH_FAULT_CURRENT=8,
  BENCH_FAULT_TIMING=9, BENCH_FAULT_STALE=10, BENCH_FAULT_NUMERIC=11,
  BENCH_FAULT_NOT_SETTLED=12, BENCH_FAULT_BAD_TARGET=13
};
typedef struct {
  int32_t encoder_count;
  int32_t target_count;
  uint32_t time_ms;
  uint32_t sample_ms;
  uint16_t command_sequence;
  uint8_t command;
  uint8_t encoder_good;
  uint8_t driver_good;
  uint8_t interlock_good;
  uint8_t estop;
  uint8_t heartbeat_good;
  float winding_current_a;
  float bus_voltage_v;
  float temperature_c;
} BenchInput;
typedef struct {
  float normalized_pwm;
  float target_current_a;
  float filtered_velocity_rad_s;
  uint8_t drive_enable;
  uint8_t state;
  uint16_t fault;
  int32_t position_error_counts;
} BenchOutput;
typedef struct {
  uint32_t ticks, last_time_ms, start_ms;
  uint16_t last_command_sequence;
  uint8_t state, started, sequence_seen;
  uint16_t fault;
  int32_t last_encoder_count, start_encoder_count, target_encoder_count;
  float filtered_velocity, velocity_reference, current_reference;
  float velocity_integral, current_integral;
} BenchCore;
void bench_init(BenchCore *core);
void bench_cycle(BenchCore *core,const BenchInput *input,BenchOutput *output);
#ifdef __cplusplus
}
#endif
#endif
