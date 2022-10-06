#!/bin/bash

bash verbose_command_wrapper.sh start "Doing a test process that should fail"
sleep 1s; $(exit 1)
bash verbose_command_wrapper.sh end $? "No errors." "Failure."

bash verbose_command_wrapper.sh start "Doing a test process that should fail again"
sleep 1s; $(exit 1)
bash verbose_command_wrapper.sh end $? "No errors." "Run failed."

bash verbose_command_wrapper.sh start "Doing a test process"
sleep 2s
bash verbose_command_wrapper.sh end $? "Run succeeded." "Run failed!"

bash verbose_command_wrapper.sh start "Doing a long test process"
sleep 8s
bash verbose_command_wrapper.sh end $? "Run succeeded." "Run failed!"
