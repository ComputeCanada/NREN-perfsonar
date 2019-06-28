provider "openstack" {}


# Instance allocation

resource "openstack_compute_instance_v2" "centralManagement" {
  name            = "centralManagement"
  image_name      = "CentOS-7-x64-2018-09"
  flavor_name     = "p4-6gb"
  key_pair        = "razer-blade"
  security_groups = ["default"]
  #user_data       = "${file("cloud-management.yaml")}" 

}


#Volume allocation

#resource "openstack_compute_volume_attach_v2" "va_1" {
  #instance_id = "${openstack_compute_instance_v2.centralManagement.id}"
  #volume_id   = "748fa7ff-c6b0-496d-9bfd-0c8eebfaa695" #Mauvais garçon qui hard-code ces valeurs.
#}


#Network Config

resource "openstack_networking_floatingip_v2" "fip_1" {
  pool = "Public-Network"
}

resource "openstack_compute_floatingip_associate_v2" "fip_1" {
  floating_ip = "${openstack_networking_floatingip_v2.fip_1.address}"
  instance_id = "${openstack_compute_instance_v2.centralManagement.id}"
}


# Outputs

output "central-management-public-address" {
  value = "${openstack_networking_floatingip_v2.fip_1.address}"
}
