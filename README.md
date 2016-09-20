karto
===========
karto is an automation script using [Fabric](http://www.fabfile.org/) to setup an OpenTopoMap server with only one command.

Current status is following [OpenTopoMap author's README](https://github.com/der-stefan/OpenTopoMap/blob/master/mapnik/HOWTO_Ubuntu_16.04). It takes currently 30 minutes (depending on your internet connection and computer) to follow all this README and load french "Rhone-Alpes" region (see Known Issues below) data.

### Usage (Linux and local LXC containers)

Just run `fab -f kartofabric.py setuplxc;setupall`. You will be asked your password once (sudo to create a local LXC container) and later container's password before deploying SSH public keys. Default `root` password is `root`, but password login is disabled during container's setup.

You can trash your container with `fab -f kartofabric.py deletelxc` if needed. Just run command above to start with a fresh container.

### Usage (plain old server with SSH access)

Assuming you can SSH to a stock Ubuntu Xenial server, you can setup it with `fab -h SERVER_IP -f kartofabric.py setupall`. You will be asked your password once (to connect to the server) before deploying SSH public keys. Password login will then be disabled during setup.

### Refreshing data

It is possible to refresh application or data with one command. Just add parameter `-h SERVER_IP` if you don't use local LXC.

`fab -f kartofabric.py updateOSMdata` : update OSM data by downloading minutly diff (will be automated soon in container)

`fab -f kartofabric.py purgeOSMdataAndReload` : erase all postgres OSM data and start a fresh new install (like after initial setup)

`fab -f kartofabric.py processlowzoom`: compute lowzoom data (monthly for example)

And less frequently, if required :

`fab -f kartofabric.py compiletirex` : Download, build and deploy fresh Tirex

`fab -f kartofabric.py installosmosis` : Download and deploy fresh Osmosis

`fab -f kartofabric.py compilemodtile` : Download, build and deploy fresh mod_tile

`fab -f kartofabric.py compileosm2pgsql` : Download, build and deploy fresh Osm2Pgsql




### Known issue

- SSH public keys are hard-coded. You must replace with your SSH keys before running the script.
- OSM region is hard-coded. Currently with French region "Rhone-Alpes".
