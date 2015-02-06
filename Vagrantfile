# -*- mode: ruby -*-
# vi: set ft=ruby :

# Vagrantfile API/syntax version. Don't touch unless you know what you're doing!
VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.box = "ubuntu/trusty64"
  config.vm.network "forwarded_port", guest: 80, host: 8080
  config.vm.network :private_network, ip: "192.168.111.222"
  config.vm.provision "ansible" do |ansible|
    ansible.limit = 'vagrant'
    ansible.playbook = "deploy/vagrant.yml"
    ansible.inventory_path = "deploy/hosts"
    ansible.ask_vault_pass = true
  end
end
