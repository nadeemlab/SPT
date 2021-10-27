#!/bin/bash

config_file='.spt_pipeline.json'
if test -f "$config_file"; then
	rm "$config_file"
fi

expect -f ./integration_tests/configure_gui.expect
