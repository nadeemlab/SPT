pip freeze | grep dgl
status=$?
[ $status -eq 0 ] || echo "Docker image for cggnn did not build and run properly."

if [ $status -eq 0 ];
then
    exit 0
else
    exit 1
fi
