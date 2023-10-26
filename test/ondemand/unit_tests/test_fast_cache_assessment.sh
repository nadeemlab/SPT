
rm -rf ../test_data/fast_cache_testing/
cp -r ../test_data/fast_cache ../test_data/fast_cache_testing

python unit_tests/fast_cache_assessment.py
status="$?"
rm -rf ../test_data/fast_cache_testing/
if [[ "$status" != "0" ]];
then
    exit "$status"
fi
