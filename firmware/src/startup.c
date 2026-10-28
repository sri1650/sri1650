#include <stdint.h>
#include "bench_core.h"
/* Cortex-M4 layout demo only: no clock, GPIO, DMA, NVIC, ADC, PWM or vendor HAL configured.
 * This image is NOT flash-ready hardware firmware. It is a reproducible ARM code-generation check. */
extern uint32_t __stack_top;
extern uint32_t __data_start__,__data_end__,__data_load__,__bss_start__,__bss_end__;
/* Minimal freestanding ABI helper: compiler can emit an ARM EABI memset call. */
void __aeabi_memclr4(void *ptr, uint32_t n){
    unsigned char *p=(unsigned char *)ptr;
    for(uint32_t i=0;i<n;++i)p[i]=0;
}
static void Default_Handler(void){for(;;){}}
static BenchCore image_state;
static BenchInput input_stub;
static BenchOutput output_stub;
volatile uint32_t compile_only_trigger;
void Reset_Handler(void){
    uint32_t *dst=&__data_start__,*src=&__data_load__;
    while(dst<&__data_end__)*dst++=*src++;
    for(dst=&__bss_start__;dst<&__bss_end__;)*dst++=0;
    bench_init(&image_state);
    for(;;){
        /* Deliberately inert without a synthetic trigger. There is no MCU peripheral hookup. */
        if(compile_only_trigger){
            compile_only_trigger=0;
            bench_cycle(&image_state,&input_stub,&output_stub);
        }
    }
}
__attribute__((used,section(".isr_vector")))
void (*const vectors[16])(void)={
  (void (*)(void))(&__stack_top),Reset_Handler,Default_Handler,Default_Handler,
  Default_Handler,Default_Handler,Default_Handler,0,0,0,0,Default_Handler,
  Default_Handler,0,Default_Handler,Default_Handler
};
