
diff -q $1 $2 1>/dev/null 2>/dev/null
if [[ "$?" == "0" ]];
then
    echo "Files exactly the same: $1 $2"
    exit 0
fi

bash ../../scripts/read-expression-dump-file.sh $1 | sort > f1
bash ../../scripts/read-expression-dump-file.sh $2 | sort > f2
diff -q f1 f2 1>/dev/null 2>/dev/null
status="$?"
if [[ "$status" == "0" ]];
then
    rm f1
    rm f2
    echo "Files the same after sorting 'lines': $1 $2"
    exit 0
else
    echo "Error"
    echo "Sorted-lines files differ: $1 $2"
    diff f1 f2
    rm f1
    rm f2
    exit 1
fi
