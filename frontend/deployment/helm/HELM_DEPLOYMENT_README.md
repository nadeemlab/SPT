# Helm deployment #

## Authorize the kubernetes cluster created with terraform ##
Now we configure your computer to communicate with your cluster 

0. Check **saml2aws** authorization
   
1. Install **[kubectl](https://kubernetes.io/docs/tasks/tools/)** on your machine
2. Check AWS CLI installation: 
   1. **which aws**
   2. **aws --version**
3. Check current identity: **aws sts get-caller-identity**
   
**IMPORTANT NOTICE! **
if you are getting errors like "error: You must be logged in to the server (Unauthorized)" you should check if you are using the same AWS account the EKS cluster was deployed with terraform. This probably can be overriden by editing aws-auth  
4. Update local *kubeconfig*: **aws eks update-kubeconfig --region us-east-1 --name spt-prod**
5. Test connection: **kubectl get svc**


## Install Helm ##

1. Install **[helm](https://helm.sh/docs/intro/install/)** on your machine 
2. Check the installation: **helm version**

## Start deploying application ##
Here we are going to need exported configuration from terraform deployment:
    ```
    terraform/tf_values_elb_prod.yaml
    terraform/tf_values_ingress_prod.yaml
    terraform/tf_values_rds_prod.yaml 
    ```
TODO manage database credentials


1. Add helm repositories for the dependencies:
    ```
    helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
    helm repo add eks https://aws.github.io/eks-charts
    helm repo update
    ```
2. Install *AWS Load Balancer* controller using [`helm_install_elb.sh`](helm_install_elb.sh).
3. Install *ingress-nginx* controller using [`helm_install_ingress_controller.sh`](helm_install_ingress_controller.sh).
4. __OPTIONAL__ Install *s3-mounter* to get cached files for spt fast-counts server:    
 
    ```
    #Check the path to configuration file tf_values_s3_mounter_prod.yaml
    helm upgrade --install s3-mounter .   \

    --namespace otomounter --create-namespace \
    -f tf_values_s3_mounter_prod.yaml
    ```
   
   // --repo https://wooferclaw.github.io/s3-mounter

  ------------------------------------
**TODO secure database secrets flow**

1.  **kubectl create secret generic db-secret \
    --from-literal=db-host=spt.cneqeknwkgdc.us-east-1.rds.amazonaws.com \
    --from-literal=db-user=apireader \
    --from-literal=db-password='Password'**

**TODO secure database secrets flow**
  ------------------------------------
  
4. Deploy the SPT application helm chart:
    ```
    TODO check the database
    #Check the directory
    cd helm
    helm upgrade --install spt . -f values.yaml
    ```

!!!! ADD INFORMATION ABOUT REROLLING INGRESS CONTROLLER!

6. Check the application deployed by the internal URL from AWS LoadBalancer. This can be found in the AWS console, which is available at URL:
```
 https://ssofed.mskcc.org/idp/startSSO.ping?PartnerSpId=urn%3Aamazon%3Awebservices
```
Current SPT backend location:
```
 https://oncopathtk.spt.aws.mskcc.org 
```


If you are getting 504 error, try to delete *ingress-nginx* pod 
```
kubectl delete pod ingress-nginx-controller-<put-correct-pod-id> -n ingress-nginx
```
and frontend pod
```
kubectl delete pod spt-frontend-<put-correct-pod-id> 
```
and refresh the browser



