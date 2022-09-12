#!/bin/bash

spt control guess-channels \
 ../test_data/./data/2779f21192cb0ce1479b2bf7fb20ebba.csv \
 ../test_data/./data/2cc18c6561b05abb1a1a95d15130a1d3.csv \
 ../test_data/./data/33c794a479e571ae50518546555b9480.csv \
 ../test_data/./data/3d25f72e8ca948280b7bfeb9de03944f.csv \
 --output=elementary_phenotypes.csv
