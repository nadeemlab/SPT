#!/bin/bash
prefix='                    '
for f in *.sh; do
    echo "$prefix$f";
    echo "$prefix$f" | tr [a-zA-Z0-9\.\_] '='
    cat $f
    echo; echo;
done
