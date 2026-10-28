#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
build="${SERVO_SANITIZER_BUILD:-/tmp/industrial-servo-asan-ubsan}"
cmake -S cpp -B "$build" -DCMAKE_BUILD_TYPE=Debug -DSERVO_ENABLE_SANITIZERS=ON
cmake --build "$build" --parallel 4
ctest --test-dir "$build" --output-on-failure
