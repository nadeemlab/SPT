#!/bin/bash

if [[ "$1" == "--help"  || "$1" == "" ]]; then
	echo "Supply the (binary format) file created by the expression matrix caching command, to parse it."
	exit
fi

xxd -c 8 -g 0 -b $1 | grep -oE ' [01]+ ' | grep -oE '[01]+' | sed 's/0/ /g'