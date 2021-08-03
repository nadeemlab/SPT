#!/bin/bash

green="\e[1;32m"
magenta="\e[1;35m"
cyan="\e[1;36m"
yellow="\e[33m"
red="\e[31m"
bold_red="\e[31;1m"
blue="\e[34m"
reset="\e[0m"

current_branch=$(git branch | grep '^* ')
if [[ "$current_branch" != "* main" ]]; then
    printf "$red""Do autoreleasing from branch main.$reset\n"
    exit
fi

release_to_branch="prerelease"

FOUND_VERSION_CHANGE=0
FOUND_ANOTHER_CHANGE=0
status=$(git status -s |
{
while IFS= read -r line
  do
    is_modified_file=$(echo "$line" | grep -oE '^ ?M')
    if [[ "$is_modified_file" == ' M' || "$is_modified_file" == 'M' ]]; then
        if [[ "$line" == ' M spatialprofilingtoolbox/version.txt' ]]; then
            FOUND_VERSION_CHANGE=1
        else
            FOUND_ANOTHER_CHANGE=1
        fi
    fi

    is_added_file=$(echo "$line" | grep -oE '^A[M ] ')
    if [[ "$is_added_file" != "" ]]; then
        FOUND_ANOTHER_CHANGE=1
    fi
done

if [[ ( "$FOUND_VERSION_CHANGE" == "1" ) && ( "$FOUND_ANOTHER_CHANGE" == "1" ) ]]; then
    printf "$red""Version has changed, but found another change. Not ready to autorelease.$reset\n"
    echo "FAILURE"
fi

if [[ ( "$FOUND_VERSION_CHANGE" == "0" ) ]]; then
    printf "$red""Version has not changed, so not ready to autorelease.$reset\n"
    printf "$yellow""Maybe you need one last commit?$reset\n"
    echo "FAILURE"
fi
} | grep -o "FAILURE" )

if [[ "$status" == "FAILURE" ]]; then
    echo "Got FAILURE"
    exit
else
    echo "Did not get FAILURE"
    exit
fi

# printf "$green""Ready to autorelease: Version is updated, and everything else under version control is unmodified.$reset\n"
# printf "$green""Building package.$reset\n"
# if test -d 'dist'; then
#     rm dist/*
# fi
# python3 -m build 1>/dev/null
# printf "$green""Built:$reset\n"
# for f in dist/*;
# do
#     printf "$yellow""    $f$reset\n"
# done
# version=$(cat spatialprofilingtoolbox/version.txt)
# printf "$green""Committing this version:$reset$yellow v$version$reset\n"
# git add spatialprofilingtoolbox/version.txt 1>/dev/null && \
#     git commit -m "Autoreleasing v$version" 1>/dev/null && \
#     git tag v$version 1>/dev/null && \
#     git push 1>/dev/null && \
#     git push origin v$version 1>/dev/null && \
#     printf "$green""Pushed v$version to remote.$reset\n" && \
#     printf "$green""Migrating updates to $release_to_branch branch.$reset\n" && \
#     rm spatialprofilingtoolbox/version.txt && \
#     git checkout $release_to_branch 1>/dev/null 2> stderr.txt && \
#     git merge main 1>/dev/null  && \
#     git push 1>/dev/null && \
#     git checkout main 1>/dev/null 2> stderr.txt && \
#     python3 -m twine upload --repository spatialprofilingtoolbox dist/* && \
#     printf "$green""Done.$reset\n"
