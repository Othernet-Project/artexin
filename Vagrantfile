# -*- mode: ruby -*-
# vi: set ft=ruby :

# Vagrantfile API/syntax version. Don't touch unless you know what you're doing!
VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.provider "virtualbox" do |vbox|
    # lxml needs more juice otherwise compilation fails badly
    vbox.memory = 1024
    vbox.cpus = 2
  end

  config.vm.define "artexin_dev" do |artexin_dev|
    artexin_dev.vm.box = "ubuntu/trusty64"

    artexin_dev.vm.network "forwarded_port", guest: 80, host: 8080

    artexin_dev.vm.provision "ansible" do |ansible|
      ansible.playbook = "deploy/vagrant.yml"
      ansible.groups = {
        "vagrant" => ["artexin_dev"]
      }
    end
  end
end
