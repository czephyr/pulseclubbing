# -*- mode: ruby -*-
# vi: set ft=ruby :
Vagrant.require_version ">= 2.0"

Vagrant.configure("2") do |config|

  config.vm.define "devpulserome" do |bs|
    bs.vm.hostname = "devpulserome"
    bs.vm.box = "debian/bullseye64"
    bs.vm.network "private_network", ip: "192.168.56.2"
    bs.vm.provider "virtualbox" do |vb|
      vb.name = "dev_vm"
      vb.memory = "2048"
    end
  end

  # Ensure that all Vagrant machines will use the same SSH key pair.
  config.ssh.insert_key = false
end