#include "bench_core.h"
/* Genuine portable embedded computation, not an STM32 peripheral/HAL implementation.
 * All output commands are SOFTWARE-ONLY and must never substitute for independent protection. */
static float clip(float x,float lo,float hi){return x<lo?lo:(x>hi?hi:x);}
static float absf(float x){return x<0?-x:x;}
static int finitef(float x){return (x==x) && x>-100000.0f && x<100000.0f;}
void bench_init(BenchCore *c){
    BenchCore z={0};*c=z;c->state=BENCH_BOOT;
}
static void fault(BenchCore *c,uint16_t reason){
    if(c->state!=BENCH_FAULT){c->state=BENCH_FAULT;c->fault=reason;}
    c->current_integral=0;c->velocity_integral=0;c->current_reference=0;c->velocity_reference=0;
}
static float quintic(float s){return s*s*s*(10.0f+s*(-15.0f+6.0f*s));}
static float quintic_derivative(float s){return s*s*(30.0f+s*(-60.0f+30.0f*s));}
void bench_cycle(BenchCore *c,const BenchInput *x,BenchOutput *out){
    const float rad_per_count=0.001963495408493621f; /* 2pi/3200 */
    BenchOutput o={0};
    ++c->ticks;
    if(!finitef(x->winding_current_a)||!finitef(x->bus_voltage_v)||!finitef(x->temperature_c))fault(c,BENCH_FAULT_NUMERIC);
    else if(x->estop)fault(c,BENCH_FAULT_ESTOP);
    else if(!x->interlock_good)fault(c,BENCH_FAULT_INTERLOCK);
    else if(!x->encoder_good)fault(c,BENCH_FAULT_ENCODER);
    else if(!x->driver_good)fault(c,BENCH_FAULT_DRIVE);
    else if(!x->heartbeat_good)fault(c,BENCH_FAULT_HEARTBEAT);
    else if(x->bus_voltage_v<18.0f || x->bus_voltage_v>29.0f)fault(c,BENCH_FAULT_BUS);
    else if(x->temperature_c>80.0f)fault(c,BENCH_FAULT_TEMP);
    else if(absf(x->winding_current_a)>1.20f)fault(c,BENCH_FAULT_CURRENT);
    else if(x->sample_ms>x->time_ms || x->time_ms-x->sample_ms>20u)fault(c,BENCH_FAULT_STALE);
    else if(c->started && (x->time_ms<=c->last_time_ms || x->time_ms-c->last_time_ms>3u)) fault(c,BENCH_FAULT_TIMING);
    if(!c->started){c->last_encoder_count=x->encoder_count;c->started=1;}
    else if(x->time_ms>c->last_time_ms){
        float dt=0.001f*(float)(x->time_ms-c->last_time_ms);
        float raw=rad_per_count*(float)(x->encoder_count-c->last_encoder_count)/dt;
        c->filtered_velocity=0.84f*c->filtered_velocity+0.16f*raw;
        c->last_encoder_count=x->encoder_count;
    }
    c->last_time_ms=x->time_ms;
    /* A new command has to have a new sequence. RESET requires all inputs safe. */
    if(x->command!=BENCH_CMD_NONE && (!c->sequence_seen || x->command_sequence!=c->last_command_sequence)){
        c->sequence_seen=1;c->last_command_sequence=x->command_sequence;
        if(x->command==BENCH_CMD_RESET){
            if(c->state==BENCH_FAULT && c->fault && !x->estop && x->interlock_good && x->encoder_good &&
               x->driver_good && x->heartbeat_good && x->bus_voltage_v>=18.0f && x->bus_voltage_v<=29.0f &&
               x->temperature_c<=80.0f && absf(x->winding_current_a)<=1.20f && x->sample_ms<=x->time_ms &&
               x->time_ms-x->sample_ms<=20u){
                c->fault=0;c->state=BENCH_READY;c->started=0;c->velocity_integral=0;c->current_integral=0;
            }
        }else if(x->command==BENCH_CMD_STOP && c->state!=BENCH_FAULT){
            c->state=BENCH_READY;c->velocity_integral=0;c->current_integral=0;
        }else if(x->command==BENCH_CMD_MOVE && (c->state==BENCH_READY || c->state==BENCH_DONE)){
            if(x->target_count < -1600 || x->target_count > 1600)fault(c,BENCH_FAULT_BAD_TARGET);
            else {
                c->start_encoder_count=x->encoder_count;
                c->target_encoder_count=x->target_count;
                c->start_ms=x->time_ms;
                c->state=BENCH_MOVING;
                c->velocity_integral=0.0f;c->current_integral=0.0f;
                c->velocity_reference=0.0f;c->current_reference=0.0f;
            }
        }
    }
    if(c->state==BENCH_BOOT)c->state=BENCH_READY;
    o.state=c->state;o.fault=c->fault;o.filtered_velocity_rad_s=c->filtered_velocity;
    o.position_error_counts=c->target_encoder_count-x->encoder_count;
    if(c->state!=BENCH_MOVING && c->state!=BENCH_DONE){*out=o;return;}
    float goal=(float)c->target_encoder_count;
    float feedforward_speed=0;
    if(c->state==BENCH_MOVING){
        float s=clip((float)(x->time_ms-c->start_ms)/1200.0f,0.0f,1.0f);
        float delta=(float)(c->target_encoder_count-c->start_encoder_count);
        goal=(float)c->start_encoder_count+delta*quintic(s);
        feedforward_speed=delta*rad_per_count*quintic_derivative(s)/1.20f;
        if(x->time_ms-c->start_ms>2500u && (absf((float)o.position_error_counts)>60.0f || absf(c->filtered_velocity)>0.35f)){
            fault(c,BENCH_FAULT_NOT_SETTLED);
            o.state=c->state;o.fault=c->fault;*out=o;return;
        }
        if(s>=1.0f && absf((float)o.position_error_counts)<32.0f && absf(c->filtered_velocity)<0.40f){
            c->state=BENCH_DONE;
        }
    }
    /* 100Hz position, 250Hz velocity, 1kHz current reference. */
    if(c->ticks%10u==0u){
        float error=(goal-(float)x->encoder_count)*rad_per_count;
        c->velocity_reference=clip(feedforward_speed+12.0f*error,-9.0f,9.0f);
    }
    if(c->ticks%4u==0u){
        float error=c->velocity_reference-c->filtered_velocity;
        float propose=c->velocity_integral+error*0.004f;
        float cmd=0.32f*error+1.2f*propose;
        if(!(cmd>0.75f && error>0.0f) && !(cmd< -0.75f && error<0.0f))c->velocity_integral=clip(propose,-0.65f,0.65f);
        c->current_reference=clip(0.32f*error+1.2f*c->velocity_integral,-0.75f,0.75f);
    }
    float emotor=0.02215414293156567f*50.0f*c->filtered_velocity;
    float error_i=c->current_reference-x->winding_current_a;
    float voltage_ff=8.0f*c->current_reference+emotor;
    float proposed_i=clip(c->current_integral+0.001f*error_i,-0.4f,0.4f);
    float proposed_v=voltage_ff+2.5f*error_i+50.0f*proposed_i;
    if(!((proposed_v>24.0f && error_i>0.0f)||(proposed_v< -24.0f && error_i<0.0f)))c->current_integral=proposed_i;
    float voltage=clip(voltage_ff+2.5f*error_i+50.0f*c->current_integral,-x->bus_voltage_v,x->bus_voltage_v);
    o.drive_enable=1;
    o.normalized_pwm=clip(voltage/x->bus_voltage_v,-1.0f,1.0f);
    o.target_current_a=c->current_reference;
    o.state=c->state;
    o.fault=c->fault;
    *out=o;
}
