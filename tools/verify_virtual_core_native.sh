#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p build/virtual_firmware
cc -std=c11 -Wall -Wextra -Werror -O1 -g \
  -I firmware/include firmware/src/bench_core.c firmware/tests/bench_native_test.c \
  -o build/virtual_firmware/bench_native_test
build/virtual_firmware/bench_native_test
if [[ "$(uname -s)" == Linux ]]; then
  cc -std=c11 -Wall -Wextra -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer \
    -I firmware/include firmware/src/bench_core.c firmware/tests/bench_native_test.c \
    -o build/virtual_firmware/bench_native_sanitized
  ASAN_OPTIONS=detect_leaks=0:halt_on_error=1 UBSAN_OPTIONS=halt_on_error=1 \
    build/virtual_firmware/bench_native_sanitized
  echo "PASS: C firmware native and AddressSanitizer/UndefinedBehaviorSanitizer"
else
  echo "PASS: C firmware native; sanitizer not run automatically on this host"
fi
