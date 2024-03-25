# Usage:
#    bash helm_install_ingress_controller.sh
#    bash helm_install_ingress_controller.sh inspect

filename=tf_values_ingress_prod.yaml
cd ../terraform/; terraform output -raw values_ingress > ../helm/$filename
cd ../helm
echo "$filename:"
echo
cat $filename

if [[ "$1" == "inspect" ]];
then
    rm $filename
    exit    
fi

helm upgrade --install ingress-nginx ingress-nginx \
 --repo https://kubernetes.github.io/ingress-nginx \
 --namespace ingress-nginx --create-namespace \
 -f $filename
rm $filename
