# Usage:
#    bash helm_install_elb.sh
#    bash helm_install_elb.sh inspect

filename=tf_values_elb_prod.yaml
cd ../terraform/; terraform output -raw values_elb > ../helm/$filename
cd ../helm
echo "$filename:"
echo
cat $filename

if [[ "$1" == "inspect" ]];
then
    rm $filename
    exit    
fi

if [[ "$1" == "uninstall" ]];
then
    rm $filename
    helm uninstall aws-load-balancer-controller eks/aws-load-balancer-controller -n kube-system
    exit
fi

helm install aws-load-balancer-controller eks/aws-load-balancer-controller -n kube-system -f $filename
rm $filename
