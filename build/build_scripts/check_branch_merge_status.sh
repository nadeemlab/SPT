#!/bin/bash

# Usage:
#     ./check_branch_merge_status.sh <branch name>
#
# Checks whether the last commit of the indicated branch is a `main` ancestor.
# Just for development convenience.

branchname="$1"
git checkout main -q
git checkout "$branchname" -q
git pull -q 2>/dev/null 1>/dev/null
status="$?"

if [[ "$status" != "0" ]];
then
    echo "You might have deleted this branch already, can't pull from remote."
    git checkout main -q
    exit 1
fi

commithash=$(git log -n 1 --pretty=format:"%H")
git checkout main -q

git --no-pager log | grep -q "$commithash"
status="$?"

if [[ "$status" == "0" ]];
then
    echo "Found most recent hash in main line: $commithash"
else
    echo "Did not find in main line: $commithash"
fi

git checkout main -q
