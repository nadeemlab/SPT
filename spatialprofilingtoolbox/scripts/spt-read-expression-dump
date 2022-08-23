#!/bin/bash

xxd -c 8 -g 0 -b $1 | grep -oE ' [01]+ ' | grep -oE '[01]+' | sed 's/0/ /g'