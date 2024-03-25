resource "aws_ec2_tag" "subnets_tag_cluster" {
   count = length(var.subnet_ids)
   resource_id = var.subnet_ids[count.index]
   key = "kubernetes.io/cluster/${var.cluster_name}"
   value = "shared"
}

resource "aws_ec2_tag" "subnets_tag_elb_internal" {
   count = length(var.subnet_ids)
   resource_id = var.subnet_ids[count.index]
   key = "kubernetes.io/role/internal-elb"
   value = "1"
}

# resource "aws_ec2_tag" "subnets_tag_elb_external" {
#    count = length(var.subnet_ids)
#    resource_id = var.subnet_ids[count.index]
#    key = "kubernetes.io/role/elb"
#    value = "1"
# }