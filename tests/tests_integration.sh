#!/bin/bash

set -e
source com.lehmannro.assert.sh/assert.sh

for script in integration_tests/*.sh;
do
    echo "$script"
    assert_raises "$script" 0
done

assert_end
