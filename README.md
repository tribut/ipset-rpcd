# ipset-rpcd

**ipset-rpcd** implements a simple JSON-RPC server that can be used together with [PacketFence](https://www.packetfence.org) and a Linux firewall. It creates IP sets that you can use to filter traffic based on a username or a user's group ("role") instead of IP addresses.

This makes firewall rules more dynamic and easier to read, much like you would expect from a *Next-Generation Firewall* appliance.

## Configuration

The behavior of **ipset-rpcd** is controlled by an ini-style text file. It maps PacketFence users and roles to one or many IP sets. It can contain the following sections:

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

By default, all IP sets are IP based only. In some circumstances, you may want to match on MAC or MAC/IP. Keys are names of IP sets, values are the `*-ENTRY` arguments to `sudo ipset add` and `sudo ipset del` respectively. The following placeholders can be used:
  * `{mac}`
  * `{ip}`

So if the IP set `role-local` was of type `bitmap:ip,mac` you would use
~~~
[ipsets]
role-local = {ip},{mac}
~~~

Note that **ipset-rpcd** sets the `comment` field of the IP set entries to the username of the respective PacketFence user, so make sure to create all ipset with the `comment` keyword (see firewall integration below).

## Parameters

**ipset-rpcd** supports the following commandline parameters

~~~
usage: ipset-rpcd.py [-h] [--bind BIND] [--port PORT] [--config CONFIG]

optional arguments:
  -h, --help       show this help message and exit
  --bind BIND      the ip address to bind to (default: 127.0.0.1)
  --port PORT      the port to listen on (default: 9090)
  --config CONFIG  config file to read ipset mapping from (default:
                   ipset.conf)
~~~

## Installation

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

### 2. Modify the configuration

You can start by using the example as a template:

~~~
cp ipset.conf.example ipset.conf
vim ipset.conf
~~~

### 3. Add the system user

~~~
adduser --system ipset-rpcd
~~~

### 4. Install the sudo rules

The sudo rules we recommend allow the daemon to add/remove entries to/from all IP sets that start with `role-` or `service-`. This is mainly a security precaution.

~~~
install -m 0440 sudoers.d/ipset-rpcd /etc/sudoers.d
~~~

Make sure your `sudoers` file contains the line `#includedir /etc/sudoers.d` for this to work or simply paste the contents of `sudoers.d/ipset-rpcd`.

### 5. Install the systemd service

~~~
install -m 0640 init/ipset-rpcd.service /etc/systemd/system
systemctl daemon-reload
~~~

To make sure the service started on boot-up, run

~~~
systemctl enable ipset-rpcd.service
~~~

You can now manually start the service using

~~~
systemctl start ipset-rpcd.service
~~~

You should now be able to reach your server locally:

~~~
curl -d '{"jsonrpc":"2.0","method":"Start","params":{"user":"lzammit","mac":"00:11:22:33:44:55","ip":"1.2.3.4","role":"default","timeout":86400},"id":42}' http://localhost:9090
~~~

### 6. Set up nginx

Install nginx and its config file

~~~
apt install nginx-light apache2-utils
install -m 0644 nginx/ipset-rpcd /etc/nginx/sites-available
~~~

Make sure to replace the certificate
~~~
vim /etc/nginx/sites-available/ipset-rpcd
~~~

And add a user for HTTP Basic auth

~~~
htpasswd -m -c nginx/htpasswd ipset-updater
~~~

Finally, enable the vhost and restart nginx

~~~
ln -s ../sites-available/ipset-rpcd /etc/nginx/sites-enabled
systemctl restart nginx
~~~

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
