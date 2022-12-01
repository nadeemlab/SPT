pip freeze | grep dgl
status=$?
[ $status -eq 0 ] || echo "Docker image for cg-gnn did not build and run properly."

if [ $status -eq 0 ];
then
    exit 0
else
    exit 1
fi
