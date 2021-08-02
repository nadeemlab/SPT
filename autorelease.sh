#!/bin/bash

current_branch=$(git branch | grep '^* ')
if [[ "$current_branch" != "* main" ]]; then
    echo "Do autoreleasing from branch main."
    exit
fi

release_to_branch="prerelease"

FOUND_VERSION_CHANGE=0
FOUND_ANOTHER_CHANGE=0
git status -s |
{
while IFS= read -r line
  do
    is_modified_file=$(echo "$line" | grep -oE '^ M ')
    if [[ "$is_modified_file" == ' M ' ]]; then
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
    echo "Version has changed, but found another change. Not ready to autorelease."
    exit
fi

if [[ ( "$FOUND_VERSION_CHANGE" == "0" ) ]]; then
    echo "Version has not changed, so not ready to autorelease. Maybe you need one last commit."
    exit
fi

if [[ ( "$FOUND_VERSION_CHANGE" == "1" ) && ( "$FOUND_ANOTHER_CHANGE" == "0" ) ]]; then
    echo "Ready to autorelease; version is updated, and everything else is the same."
    echo "Building package."
    if test -d 'dist'; then
        rm dist/*
    fi
    python3 -m build 1>/dev/null
    echo "Built:"
    for f in dist/*;
    do
        echo "    $f"
    done
    version=$(cat spatialprofilingtoolbox/version.txt)
    echo "Committing this version: v$version"
    git add spatialprofilingtoolbox/version.txt && \
        git commit -m "Autoreleasing v$version" && \
        git tag v$version && \
        git push 1>/dev/null && \
        git push origin v$version && \
        echo "Pushed v$version to remote." && \
        echo "Migrating updates to $release_to_branch branch." && \
        rm spatialprofilingtoolbox/version.txt && \
        git checkout $release_to_branch && \
        git merge main && \
        git push 1>/dev/null && \
        git checkout main && \
        python3 -m twine upload --repository spatialprofilingtoolbox dist/*
fi
}
