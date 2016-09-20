from fabric.api import *
from fabric.contrib import files
from fabric.context_managers import shell_env
import time
import string

SSH_KEYS = [
	"ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEAw9R1/dJA3wrhZ5fCTWBg5gVZhfleWQJ6bDMfplTZ7TjCYuq0/KkjYGGAxB4IplR0NMeVAjfrs2RWMuUSwDmI3Fr+y1xVrHWdwpESciOvx7k0YnVhETIxbLmnVCSkcTzyYCjdmQvxNwElkr55TEt+1zVpWMNTx9d5bNjcgXoaZyqAM4PTF2O9KCOiUOVsiklygCM6GY4dVAC/Z3+Xhsp4/q/wojGlNEzjtKQAD6OXD3ogmQl9TPAURo7QdOtGhIYo6sp7eq4XtsdidSHCNPaXsS4d6MM9+LTXtVlxzoBwRFiw4k/625BCLj4RnlDbu+vBvY6ZtCnj5I/rRm7MQsIC+w== martin",
	"ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQC/yScc+iTX7/vGVpLo6HimwMyDG1c6tyCgiua9CFbgi6bIq8RU/hE9WQaFbR+pZZUaBGodi557SplVwLoRqRXzA6IoBaIOGkQDqNKU6V+IH46djrS6rNUpW++iMrbawjHyCob7pQ4As2fZy3fdBW0/oCc0rTP6M5vAbYnsSWwOrGy5861xhvsXXn/ELt/DMVwcaAxrs6CCZISXpGFpFe/KKAFw38DIlhNgjmG0P9NnPmUPh3fWi49bvzlvjFrRlG1YAAOX1fT7Oi8uJlGLnDZpfHGu5BKjEBBfiPIKK+3GhJPSF/ZF4H8JTs7rXzkHkIEdTsu8oHPG++UQWiXNpk3YHb8JlLvHY76jP+4bwXX++rFrXfQnsVwtbeZlh3Re8+1ZBhyYJAmzgR48KNjMKOmdatzbQwF9QnBCCXIxifVKMHcafdN7FhH8ZvMhlPMgLYn/FpFBSRXFIafEfF7R6QsqyTX1F0EgyTC6RDbS/qAGaHyorHYAmur6FexyRKLZTi/yPIIWYfQ7HWZu9SrDfAXK6CKKGhZhnKoBXYv7CEKOfbxGuhIMIfieInvUdD7dSDxI/0MAphYnM4qwJs95JtwAscbWdSAzMsZg82lqDN88wQ3VG8q708+bIuFCKGYOyNsd/AJ0S4m1pHsylnQq4LAZ8lgd44nCPCO9BNuyheTuwQ== valentin"
]

PACKAGES = [
	"postgresql",
	"language-pack-fr",
	"postgresql-contrib",
	"postgis",
	"vim",
	"git",
	"apache2",
	# Mapnik
	"libmapnik3.0",
	"libmapnik-dev",
	"mapnik-utils",
	"python-mapnik",
	# Requirements Tyrex source
	"devscripts",
	"libjson-perl",
	"libipc-sharelite-perl",
	"libgd-perl debhelper",
	# Requirements modtile
	"autoconf",
	"apache2-dev",
	# Requirements osm2pgsql
	"cmake",
	"libbz2-dev",
	"libgeos-dev",
	"libgeos++-dev",
	"libproj-dev",
	"lua5.3 liblua5.3-dev",
	# Osmosis
	"default-jre-headless",
	"junit"
]

# Get LXC ip
env.hosts = local("sudo lxc-info -n kartolxc | grep IP | awk '{ print $2 }'",capture=True)

def setuplxc():
	local("sudo lxc-create -t download -n kartolxc -- --dist ubuntu --release xenial --arch amd64")
	local("sudo lxc-start -n kartolxc")
	while '' == local("sudo lxc-info -n kartolxc | grep IP | awk '{ print $2 }'",capture=True) :
		time.sleep(1)
	local("sudo lxc-attach -n kartolxc -- apt-get install --assume-yes openssh-server")
	local("sudo lxc-attach -n kartolxc -- bash -c \"echo 'root:root'|chpasswd\"")
	local("sudo lxc-attach -n kartolxc -- sed -i 's/^PermitRootLogin .*/PermitRootLogin yes/g' /etc/ssh/sshd_config")
	local("sudo lxc-attach -n kartolxc -- service ssh restart")
	local("sudo lxc-info -n kartolxc | grep IP | awk '{ print $2 }'")

def deletelxc():
	local("sudo lxc-stop -n kartolxc")
	local("sudo lxc-destroy -n kartolxc")

def sshd():
	with settings(user="root"):
		run("sudo useradd -m -g users -s /bin/bash -p test karto")
		run("echo 'karto:karto'|chpasswd")
		run("mkdir -p /root/.ssh")
		for key in SSH_KEYS:
			files.append("/root/.ssh/authorized_keys", key)
		files.sed("/etc/ssh/sshd_config", "#?\s*PasswordAuthentication\s*(no|yes)", "PasswordAuthentication no")
		run("mkdir -p /home/karto/.ssh && chown -Rf karto:users /home/karto/.ssh")
		for key in SSH_KEYS:
			files.append("/home/karto/.ssh/authorized_keys", key)
		run("service ssh restart")

def aptget():
	with settings(user="root"):
		run("apt-get --quiet update")
		run("apt-get --quiet -y upgrade")
		run("apt-get --quiet -y install unattended-upgrades")
		files.append("/etc/apt/apt.conf.d/20auto-upgrades", """APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";""") # because dpkg-reconfigure --priority=low unattended-upgrades has a prompt

def packages():
	with settings(user="root"):
		run("apt-get --quiet -y install %s" % " ".join(PACKAGES))

def configpostgres():
	with settings(user="root"):
		files.sed("/etc/postgresql/9.5/main/postgresql.conf", "#?\s*shared_buffers.*", "shared_buffers = 256MB")
		files.sed("/etc/postgresql/9.5/main/postgresql.conf", "#?\s*work_mem.*", "work_mem = 256MB")
		files.sed("/etc/postgresql/9.5/main/postgresql.conf", "#?\s*maintenance_work_mem.*", "maintenance_work_mem = 256MB")
		files.sed("/etc/postgresql/9.5/main/postgresql.conf", "#?\s*autovacuum.*", "autovacuum = off")
		run("service postgresql restart")
		run("mkdir -p /var/lib/postgresql/.ssh && chown -Rf postgres /var/lib/postgresql/.ssh")
		for key in SSH_KEYS:
			files.append("/var/lib/postgresql/.ssh/authorized_keys", key)

def postgresinitdb():
	with settings(user="postgres"):
		run("createuser --createdb karto")
		run("createdb gis")
		run("psql -d gis -c 'CREATE EXTENSION postgis;'")

def postgresdropdb():
	with settings(user="postgres"):
		run("psql -d template1 -c 'DROP DATABASE IF EXISTS gis'")
		run("dropuser karto")


def compiletirex():
	with settings(user="karto"):
		run("mkdir -p /home/karto/src/")
		with cd("/home/karto/src/"):
			run("rm -Rf tirex tirex* tirex*.deb")
			run("git clone https://github.com/geofabrik/tirex")
		with cd("/home/karto/src/tirex"):
			run("make deb")
		with cd("/home/karto/src/"):
			with settings(user="root"):
				run("dpkg -i tirex-core*.deb tirex-backend-mapnik*.deb")

def installosmosis():
	with settings(user="karto"):
		run("rm -Rf /home/karto/src/osmosis")
		run("mkdir -p /home/karto/src/osmosis")
		with cd("/home/karto/src/osmosis"):
			run("wget -qO- http://bretth.dev.openstreetmap.org/osmosis-build/osmosis-latest.tgz | tar -xvzf -")
			run("chmod a+x bin/osmosis")
	with settings(user="root"):
		run("rm -Rf /usr/local/bin/osmosis")
		run("ln -s /home/karto/src/osmosis/bin/osmosis /usr/local/bin/osmosis")


def compilemodtile():
	with settings(user="karto"):
		run("mkdir -p /home/karto/src/")
		with cd("/home/karto/src/"):
			run("rm -Rf mod_tile libapache2-mod-tile*.deb")
			run("git clone git://github.com/openstreetmap/mod_tile.git")
		with cd("/home/karto/src/mod_tile"):
			run("echo '/etc/renderd.conf' > debian/renderd.conffiles")
			files.comment("/home/karto/src/mod_tile/debian/tileserver_site.conf", "LoadTileConfigFile")
			files.sed("/home/karto/src/mod_tile/debian/tileserver_site.conf", "#?\s*ModTileRenderdSocketName.*", "    ModTileRenderdSocketName /var/lib/tirex/modtile.sock")
			run("debuild -i -b -us -uc")
	with settings(user="root"):
		with cd("/home/karto/src/"):
			run("echo 'libapache2-mod-tile libapache2-mod-tile/enablesite boolean false' | debconf-set-selections")
			run("dpkg -i libapache2-mod-tile*.deb")	
		run("a2enmod tile")
		run("a2dissite 000-default")
		run("a2ensite tileserver_site")
		run("rm -rf /var/lib/mod_tile")
		run("ln -s /var/lib/tirex/tiles /var/lib/mod_tile")
		run("service apache2 restart")

def compileosm2pgsql():
	with settings(user="karto"):
		run("mkdir -p /home/karto/src/")
		with cd("/home/karto/src/"):
			run("rm -Rf osm2pgsql")
			run("git clone git://github.com/openstreetmap/osm2pgsql.git")
		with cd("/home/karto/src/osm2pgsql"):
			run("mkdir build")
		with cd("/home/karto/src/osm2pgsql/build"):
			run("cmake ..")
			run("make")
			with settings(user="root"):
				run("make install")

def installopentopomap():
	with settings(user="karto"):
		with cd("/home/karto/"):
			run("rm -Rf OpenTopoMap")
			run("git clone https://github.com/der-stefan/OpenTopoMap/")
def loadinitialOSMdata():
	with settings(user="karto"):
		run("mkdir -p /home/karto/data/update")
		#put("rhone-alpes-latest.osm.pbf","/home/karto/data/rhone-alpes-latest.osm.pbf")
		#put("state.txt","/home/karto/data/update/state.txt")
		with cd("/home/karto/data/"):
			run("wget http://download.geofabrik.de/europe/france/rhone-alpes-latest.osm.pbf")
		with cd("/home/karto/data/update/"):
			run("wget http://download.geofabrik.de/europe/france/rhone-alpes-updates/state.txt")
		run("osm2pgsql --slim -d gis -C 12000 --number-processes 10 --flat-nodes /home/karto/gis-flat-nodes.bin --style ~/OpenTopoMap/mapnik/osm2pgsql/opentopomap.style ~/data/rhone-alpes-latest.osm.pbf")
		run("osmosis --rrii workingDirectory=~/data/update")
		files.sed("/home/karto/data/update/configuration.txt", "#?\s*baseUrl.*", "baseUrl=http://download.geofabrik.de/europe/france/rhone-alpes-updates/")
		files.sed("/home/karto/data/update/configuration.txt", "#?\s*maxInterval.*", "maxInterval=0")

def updateOSMdata():
	with settings(user="karto"):
		run("osmosis --rri workingDirectory=~/data/update --simplify-change --write-xml-change ~/data/update/changes.osc.gz")
		run("osm2pgsql --append --slim -d gis  -C 12000 --number-processes 10 --flat-nodes /home/karto/gis-flat-nodes.bin --style ~/OpenTopoMap/mapnik/osm2pgsql/opentopomap.style ~/data/update/changes.osc.gz")
		run("rm ~/data/update/changes.osc.gz")

def purgeOSMdataAndReload():
	with settings(user="karto"):
		run("rm -Rf /home/karto/data")
		run("rm -Rf /home/karto/gis-flat-nodes.bin")
	postgresdropdb()
	postgresinitdb()
	loadinitialOSMdata()
	updateOSMdata()

def setupall():
	sshd()
	aptget()
	packages()
	configpostgres()
	compiletirex()
	compilemodtile()
	compileosm2pgsql()
	postgresinitdb()
	installopentopomap()
	installosmosis()
	loadinitialOSMdata()
	updateOSMdata()
