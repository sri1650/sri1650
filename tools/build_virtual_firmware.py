"""Compile a portable firmware control core for host SIL and a Cortex-M4 compile-only ELF."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]

def build(output:Path,arm:bool=True,require_arm:bool=False)->dict:
    output.mkdir(parents=True,exist_ok=True)
    include=ROOT/'firmware/include'
    src=ROOT/'firmware/src/bench_core.c'
    host=output/('libbench_core.dylib' if sys.platform=='darwin' else 'libbench_core.so')
    dylib_flag='-dynamiclib' if sys.platform=='darwin' else '-shared'
    subprocess.run(['cc','-std=c11','-O2','-fPIC','-Wall','-Wextra','-Werror',dylib_flag,'-I',str(include),str(src),'-o',str(host)],check=True)
    result={'host_shared_library':str(host.relative_to(ROOT)),'arm_compile_only':False}
    clang=shutil.which('clang')
    if arm and clang:
        elf=output/'bench_m4_compile_only.elf'
        cmd=[clang,'--target=arm-none-eabi','-mcpu=cortex-m4','-mthumb',
             '-mfpu=fpv4-sp-d16','-mfloat-abi=hard','-Os','-ffreestanding',
             '-fdata-sections','-ffunction-sections','-nostdlib','-fuse-ld=lld',
             '-I',str(include),'-Wl,--gc-sections',
             '-Wl,-T,'+str(ROOT/'firmware/toolchain/stm32g474re_compile_only.ld'),
             '-Wl,-Map,'+str(output/'bench_m4_compile_only.map'),
             str(src),str(ROOT/'firmware/src/startup.c'),'-o',str(elf)]
        try:
            subprocess.run(cmd,check=True,capture_output=True,text=True)
            if elf.read_bytes()[18]!=40:raise RuntimeError('ELF e_machine should be ARM (40)')
            result.update({'arm_compile_only':True,'target':'Cortex-M4 ARM EABI',
                           'arm_elf':str(elf.relative_to(ROOT)),'arm_elf_bytes':elf.stat().st_size})
        except (OSError,subprocess.CalledProcessError) as error:
            if require_arm:raise
            result['arm_unavailable_reason']=str(error)[:600]
    elif arm and require_arm:
        raise RuntimeError('LLVM clang missing: Cortex-M4 code generation required')
    (output/'build_manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--no-arm',action='store_true');p.add_argument('--require-arm',action='store_true');a=p.parse_args()
    print(json.dumps(build(ROOT/'build/virtual_firmware',arm=not a.no_arm,require_arm=a.require_arm),indent=2))
