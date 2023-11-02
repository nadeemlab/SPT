
exceeded=$(python unit_tests/timeout.py 2>&1 | grep 'Ondemand timeout [0-9]\+\.[0-9]\+ exceeded')
if [[ "$exceeded" == ""  ]];
then
    echo "Timeout was not triggered in this controlled setting."
    exit 1
else
    echo "($exceeded)"
    echo "Timeout was triggered as expected."
fi
