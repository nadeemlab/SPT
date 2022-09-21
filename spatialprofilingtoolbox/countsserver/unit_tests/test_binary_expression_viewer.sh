
bash scripts/read-expression-dump-file.sh > signature_array.txt
unit_tests/signature_array.0.1.txt

diff unit_tests/signature_array.0.1.txt signature_array.txt
status=$?
[ $status -eq 0 ] && echo "Binary expression format read operation is accurate." || echo "Binary expression read operation failed."
rm signature_array.txt

if [ $status -eq 0 ];
then
    exit 0
else
    exit 1
fi
