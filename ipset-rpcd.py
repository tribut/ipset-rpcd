from jsonrpclib.SimpleJSONRPCServer import SimpleJSONRPCServer
import subprocess

EXIT_OK = ["OK"]  # We need to always return an array


def start(user, mac, ip, role, timeout):
    print((
        'Updating entry for {user} ({mac}, {ip}, {role}) '
        'with timeout {timeout}').format(
        user=user, mac=mac, ip=ip, role=role, timeout=timeout))
    ret = subprocess.run([
        "sudo", "ipset", "add", "-exist",
        "role-{}".format(role),
        "{ip},{mac}".format(ip=ip, mac=mac),
        "timeout", timeout,
        "comment", user,
        ])
    return EXIT_OK if ret.returncode == 0 else ["Error"]


def stop(user, mac, ip, role, timeout):
    print((
        'Removing entry for {user} ({mac}, {ip}, {role}) '
        'with timeout {timeout}').format(
        user=user, mac=mac, ip=ip, role=role, timeout=timeout))
    ret = subprocess.run([
        "sudo", "ipset", "del", "-exist",
        "role-{}".format(role),
        "{ip},{mac}".format(ip=ip, mac=mac),
        ])
    return EXIT_OK if ret.returncode == 0 else ["Error"]


if __name__ == '__main__':
    server = SimpleJSONRPCServer(('localhost', 9090))
    server.register_function(start, 'Start')
    server.register_function(start, 'Update')
    server.register_function(stop, 'Stop')
    server.serve_forever()
