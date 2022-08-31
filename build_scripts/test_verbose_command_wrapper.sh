#!/bin/bash

bash verbose_command_wrapper.sh start "Doing a test process that should fail"
sleep 1s
$(exit 1)
result_code=$?
bash verbose_command_wrapper.sh end $result_code "No errors." "Failure."

bash verbose_command_wrapper.sh start "Doing a test process that should fail again"
sleep 1s
$(exit 1)
result_code=$?
bash verbose_command_wrapper.sh end $result_code "No errors." "Run failed."

bash verbose_command_wrapper.sh start "Doing a test process"
sleep 2s
result_code=$?
bash verbose_command_wrapper.sh end $result_code "Run succeeded." "Run failed!"

bash verbose_command_wrapper.sh start "Doing a long test process"
sleep 8s
result_code=$?
bash verbose_command_wrapper.sh end $result_code "Run succeeded." "Run failed!"
