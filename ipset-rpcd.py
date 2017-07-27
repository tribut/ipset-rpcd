from jsonrpclib.SimpleJSONRPCServer import SimpleJSONRPCServer
import six
import subprocess
import logging
import argparse
from six.moves import configparser
import signal


class Ipset_rpcd:
    """daemon which updates ipsets based on events it receives via JSON-RPC"""

    OK = ["OK"]  # We need to always return an array
    ERROR = ["Error"]

    def __init__(self):
        # Setup logging
        logging.basicConfig(level=logging.DEBUG)

        # Parse commandline
        self.parser = argparse.ArgumentParser(
            description="IPset JSON-RPC daemon",
            epilog="Config file is reloaded on SIGUSR1",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        self.parser.add_argument("--bind", default="127.0.0.1",
                                 help="the ip address to bind to")
        self.parser.add_argument("--port", type=int, default="9090",
                                 help="the port to listen on")
        self.parser.add_argument("--config", default="ipset.conf",
                                 help="config file to read ipset mapping from")
        self.args = self.parser.parse_args()

        # Init config
        self.config = configparser.ConfigParser()
        self._read_config()

        # Setup config reloading
        def reload(signal, frame):
            self._read_config()
        signal.signal(signal.SIGUSR1, reload)

        # Init server
        self.server = SimpleJSONRPCServer((self.args.bind, self.args.port))

        # Register handlers
        def start(*args, **kw):
            self._start(*args, **kw)

        def stop(*args, **kw):
            self._stop(*args, **kw)

        self.server.register_function(start, "Start")
        self.server.register_function(start, "Update")
        self.server.register_function(stop, "Stop")

    def serve_forever(self):
        logging.info(
            "Starting ipset JSON-RPC daemon at {bind}:{port}...".format(
                bind=self.args.bind,
                port=self.args.port,
                )
            )
        try:
            self.server.serve_forever()
        except KeyboardInterrupt:
            logging.info("Stopped")

    def _read_config(self):
        # create new config object, so that old entries are removed
        newconfig = configparser.ConfigParser()
        logging.debug("Reading config {}".format(self.args.config))
        if not newconfig.read(self.args.config):
            logging.error("Could not load config!")
        else:
            self.config = newconfig

    def _start(self, user, mac, ip, role, timeout):
        logging.info((
            "Updating entries for {user} ({mac}, {ip}, {role}) "
            "with timeout {timeout}").format(
            user=user, mac=mac, ip=ip, role=role, timeout=timeout))

        action = "add"
        okay = self._update_user(**locals())

        return self.OK if okay else self.ERROR

    def _stop(self, user, mac, ip, role, timeout):
        logging.info((
            "Removing entries for {user} ({mac}, {ip}, {role}) "
            ).format(
            user=user, mac=mac, ip=ip, role=role))

        action = "remove"
        okay = self._update_user(**locals())

        return self.OK if okay else self.ERROR

    def _update_user(self, action, user, mac, ip, role, timeout):
        args = locals().copy()

        try:
            roles = [
                role.strip()
                for role in self.config.get("roles", role).split(",")
                ]
        except (configparser.NoOptionError, configparser.NoSectionError) as e:
            roles = []

        try:
            services = [
                user.strip()
                for user in self.config.get("users", user).split(",")
                ]
        except (configparser.NoOptionError, configparser.NoSectionError) as e:
            services = []

        okay = True
        for ipset in roles + services:
            args.update({"ipset": ipset})
            if not self._update_ipset(**args):
                okay = False
        return okay

    def _update_ipset(self, ipset, action, user, mac, ip, role, timeout):
        if action not in ["add", "remove"]:
            logging.error("Unknown action {}".format(action))
            return False

        try:
            items = self.config.get("ipsets", ipset)
        except (configparser.NoOptionError, configparser.NoSectionError) as e:
            items = "{ip}"

        logging.debug((
            "User {user}: {action} ipset {ipset} with items {items}").format(
            user=user, action=action, ipset=ipset, items=items))

        args = [
            "sudo", "-n", "ipset",
            str(action), "-exist", str(ipset),
            items.format(ip=ip, mac=mac)
            ]

        if action == "add":
            args = args + [
                "timeout", str(timeout),
                "comment", str(user)
                ]

        ret = subprocess.call(args)
        return ret == 0


if __name__ == "__main__":
    ipset_rpcd = Ipset_rpcd()
    ipset_rpcd.serve_forever()
