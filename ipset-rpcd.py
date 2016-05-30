from jsonrpclib.SimpleJSONRPCServer import SimpleJSONRPCServer
import subprocess
import logging

EXIT_OK = ["OK"]  # We need to always return an array


def start(user, mac, ip, role, timeout):
    logging.info((
        'Updating entry for {user} ({mac}, {ip}, {role}) '
        'with timeout {timeout}').format(
        user=user, mac=mac, ip=ip, role=role, timeout=timeout))
    ret = subprocess.call([
        "sudo", "ipset", "add", "-exist",
        "role-{}".format(role),
        "{ip},{mac}".format(ip=ip, mac=mac),
        "timeout", str(timeout),
        "comment", str(user),
        ])
    return EXIT_OK if ret == 0 else ["Error"]


def stop(user, mac, ip, role, timeout):
    logging.info((
        'Removing entry for {user} ({mac}, {ip}, {role}) '
        'with timeout {timeout}').format(
        user=user, mac=mac, ip=ip, role=role, timeout=timeout))
    ret = subprocess.call([
        "sudo", "ipset", "del", "-exist",
        "role-{}".format(role),
        "{ip},{mac}".format(ip=ip, mac=mac),
        ])
    return EXIT_OK if ret == 0 else ["Error"]

logging.basicConfig(level=logging.DEBUG)

if __name__ == '__main__':
    logging.info("Starting JSON-RPC daemon...")
    server = SimpleJSONRPCServer(('localhost', 9090))
    server.register_function(start, 'Start')
    server.register_function(start, 'Update')
    server.register_function(stop, 'Stop')
    server.serve_forever()
