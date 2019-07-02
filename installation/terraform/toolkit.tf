# Instance allocation

resource "openstack_compute_instance_v2" "toolkit" {
  name            = "toolkit"
  image_name      = "CentOS-7-x64-2018-09"

  flavor_name     = "p4-6gb"
  key_pair        = "razer-blade"
  security_groups = ["default"]
  #user_data       = "${file("cloud-toolkit.yaml")}" 

}


#Network Config

resource "openstack_networking_floatingip_v2" "fip_2" {
  pool = "Public-Network"
}

resource "openstack_compute_floatingip_associate_v2" "fip_2" {
  floating_ip = "${openstack_networking_floatingip_v2.fip_2.address}"
  instance_id = "${openstack_compute_instance_v2.toolkit.id}"
}


#Auto add record
resource "cloudflare_record" "record_toolkit" {
  domain = "paspirine.xyz"
  name   = "toolkit"
  value  = "${openstack_networking_floatingip_v2.fip_2.address}"
  type   = "A"
  ttl    = 1
}
