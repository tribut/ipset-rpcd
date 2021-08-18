# ipset-rpcd

[<img alt="JSONRPC-Settings in PacketFence" src="https://github.com/inverse-inc/packetfence/blob/8e46dba6b23606c35c1e04f4ecc23aceb1e66d61/docs/images/doc-jsonrpc-cfg_SSO_pf.png" width="400" align="right">][PacketFence Guide]

**ipset-rpcd** implements a simple JSON-RPC server that can be used together with [PacketFence] and a Linux firewall. It creates IP sets that you can use to **filter traffic based on a username or a user's group** ("role") instead of IP addresses.

This makes firewall rules more dynamic and easier to read, much like you would expect from a *Next-Generation Firewall* appliance.

## Table of Contents

  1. [Install guide](#install-guide)
  1. [Command-line arguments](#command-line-arguments)
  1. [Configuration](#configuration)
  1. [Firewall Integration](#firewall-integration)
  1. [Credits](#credits)

## Install guide

### Overview

The server calls `sudo ipset [...]` to modify the IP sets according to the configuration file. Corresponding sudo rules are provided.
To keep the code simple, **ipset-rpcd** does not provide encryption or authentication, so we recommend using **nginx** as a reverse proxy for TLS termination and auth.
We also provide a **systemd** service file to handle running of the daemon.

The following instructions assume Debian/Ubuntu system but should be very similar on any Linux distribution.

### 1. Get the code

Login to your firewall as root and run

~~~
umask 022
mkdir -p /opt/stunet
cd /opt/stunet
git clone https://github.com/tribut/ipset-rpcd.git
~~~

### 2. Install Python Dependencies

At the moment this should just be one module.

~~~
pip3 install -r requirements.txt
~~~

### 3. Modify the configuration

You can start by using the example as a template. See below for a [comprehensive guide on the config file syntax](#configuration).

~~~
cp ipset.conf.example ipset.conf
vim ipset.conf
~~~

### 4. Add the systemd service and sudo rules

~~~
adduser --system ipset-rpcd
install -m 0640 init/ipset-rpcd.service /etc/systemd/system
systemctl daemon-reload
systemctl enable ipset-rpcd.service
~~~

The sudo rules we recommend allow the daemon to add/remove entries to/from all IP sets that start with `role-` or `service-`. This is mainly a security precaution.

~~~
install -m 0440 sudoers.d/ipset-rpcd /etc/sudoers.d
~~~

Make sure your `sudoers` file contains the line `#includedir /etc/sudoers.d` for this to work or paste the contents of `sudoers.d/ipset-rpcd` alternatively.

You can now manually start the service and should be able to test your server locally:

~~~
systemctl start ipset-rpcd.service
curl -d '{"jsonrpc":"2.0","method":"Start","params":{"user":"lzammit","mac":"00:11:22:33:44:55","ip":"1.2.3.4","role":"default","timeout":86400},"id":42}' http://localhost:9090
~~~

### 5. Set up nginx

Install nginx and its config file

~~~
apt install nginx-light apache2-utils
install -m 0644 nginx/ipset-rpcd /etc/nginx/sites-available
vim /etc/nginx/sites-available/ipset-rpcd
~~~

Make sure to replace the certificate, then add a user for HTTP Basic auth

~~~
htpasswd -m -c nginx/htpasswd ipset-updater
~~~

Finally, enable the vhost and restart nginx

~~~
ln -s ../sites-available/ipset-rpcd /etc/nginx/sites-enabled
systemctl restart nginx
~~~

### 6. Enable SSO in PacketFence

A short [guide on how to set up PacketFence SSO with ipset-rpcd][PacketFence Guide] is available on the PacketFence website.

## Command-line arguments

**ipset-rpcd** supports the following command-line arguments:

~~~
usage: ipset-rpcd.py [-h] [--bind BIND] [--port PORT] [--config CONFIG]

optional arguments:
  -h, --help       show this help message and exit
  --bind BIND      the ip address to bind to (default: 127.0.0.1)
  --port PORT      the port to listen on (default: 9090)
  --config CONFIG  config file to read ipset mapping from (default:
                   ipset.conf)
~~~

## Configuration

The behavior of **ipset-rpcd** is controlled by an ini-style text file, which is read on startup and on SIGUSR1 (`systemctl reload ipset-rpcd.service`).

It maps PacketFence users and roles to one or many IP sets. It can contain the following sections:

### roles

Assign IP sets to PacketFence roles. Keys are the roles, values are the name of an IP set or multiple IP sets, separated by commas. So if you wanted members of roles `staff` and `admin` in an IP set named `role-staff`, but users with role `admin` should also be in the ipset `role-admin`, you would use:

~~~
[roles]
staff = role-staff
admin = role-staff, role-admin
~~~

### users

Assign IP sets to individual PacketFence users. Keys are usernames, values are the name of an IP set or multiple IP sets, separated by commas. So if you want the user `johndoe` to be added to the
IP sets `service-http` and `service-proxy` you would use:

~~~
[users]
johndoe = service-http, service-proxy
~~~

### ipsets

By default, *all IP sets are IP-based*. In some circumstances, you may want to match on MAC or MAC/IP.

Keys are names of IP sets, values are the `*-ENTRY` arguments to `sudo ipset add` and `sudo ipset del` respectively. The following placeholders can be used:
  * `{mac}`
  * `{ip}`

So if the IP set `role-local` was of type `bitmap:ip,mac` you would use
~~~
[ipsets]
role-local = {ip},{mac}
~~~

Note that **ipset-rpcd** sets the `comment` field of the IP set entries to the username of the respective PacketFence user, so make sure to create all ipset with the `comment` keyword (see firewall integration below).

## Firewall integration

### Shorewall

When you run shorewall, you can use it to create the IP sets on startup and easily match traffic:

**shorewall.conf**
~~~
SAVE_IPSETS=No
~~~

**init**
~~~
ipset -exist create role-admin bitmap:ip,mac range 192.168.1.0-192.168.10.255 timeout 21600 comment
ipset -exist create service-http hash:ip timeout 21600 comment
~~~

**rules**
~~~
HTTP(ACCEPT) all              user:+service-http
SSH(ACCEPT)  user:+role-admin mgnt
~~~

## Credits

**ipset-rpcd** was created for [StuNet Freiberg](https://www.stunet.tu-freiberg.de/) by [Felix Eckhofer](mailto:felix@eckhofer.com). Please get in touch with any feedback!


[PacketFence]: https://www.packetfence.org
[PacketFence Guide]: https://www.packetfence.org/doc/PacketFence_Installation_Guide.html#_json_rpc
