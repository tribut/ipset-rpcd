from jsonrpclib.SimpleJSONRPCServer import SimpleJSONRPCServer
import subprocess
import logging
import argparse

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


if __name__ == '__main__':
    # Setup logging
    logging.basicConfig(level=logging.DEBUG)

    # Parse commandline
    parser = argparse.ArgumentParser(
        description='JSON-RPC daemon',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--bind', default='127.0.0.1',
                        help='set the ip address to bind to')
    parser.add_argument('--port', type=int, default='9090',
                        help='set the port to listen on')
    args = parser.parse_args()

    # Start server
    logging.info("Starting JSON-RPC daemon at {bind}:{port}...".format(
        bind=args.bind,
        port=args.port,
    ))
    server = SimpleJSONRPCServer((args.bind, args.port))
    server.register_function(start, 'Start')
    server.register_function(start, 'Update')
    server.register_function(stop, 'Stop')
    server.serve_forever()
