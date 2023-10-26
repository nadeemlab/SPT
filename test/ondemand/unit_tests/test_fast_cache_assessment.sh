
rm -rf ../test_data/fast_cache_testing/
cp -r ../test_data/fast_cache ../test_data/fast_cache_testing

python unit_tests/fast_cache_assessment.py
if [[ "$1" != "0" ]];
then
    exit 1
fi
rm -rf ../test_data/fast_cache_testing/
