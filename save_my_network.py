#!/usr/bin/python
import os
import sys
import shlex
from subprocess import Popen, PIPE, STDOUT

# Set to True to save the rule numbers
INCLUDE_RULE_NUMBER = False


class Result:
    pass


def cmd_noerror(command):
    result = Result()

    p = Popen(shlex.split(command), stdin=PIPE, stdout=PIPE, stderr=PIPE)
    (stdout, stderr) = p.communicate()

    result.exit_code = p.returncode
    result.stdout = stdout
    result.stderr = stderr
    result.command = command

    return result


out_line = []
startup_file = 'network.save'


def save_network_on_file():
    interfaces = os.listdir('/sys/class/net/')
    command = ["#!/bin/bash\n"]
    for interface in interfaces:
        ip_address = cmd_noerror("ip -4 -o addr show "+interface)
        ip_address = ip_address.stdout.split()

        def get_indexes(ip_address, xs): return [i for (y, i) in zip(xs, range(
            len(xs))) if ip_address == y]  # get all indexes of inet in ip_address list

        inet_number = (get_indexes(b"inet", ip_address))
        for inet in inet_number:
            ip_address_elemnt = inet + 1
            ip_prefix = ip_address[ip_address_elemnt]
            single_command = "ip addr add " + \
                str(ip_prefix)+" dev "+interface+"\n"
            command.append(single_command)
        flags_file = open("/sys/class/net/"+interface+"/flags", "r")
        flags = flags_file.read().strip()
        flags_file.close()
        single_command = "echo "+flags+" > /sys/class/net/"+interface+"/flags\n"
        command.append(single_command)
    route = cmd_noerror("ip route list")
    route = route.stdout
    route = route.splitlines()
    for line in route:
        command.append("ip route add "+line.decode("utf-8") + "\n")

    rule = cmd_noerror("ip rule list")
    rule = rule.stdout
    rule = rule.splitlines()
    for line in rule:
        if INCLUDE_RULE_NUMBER is False:
            line = line.decode("utf-8").split(':')[1].strip()
        else:
            line = line.decode("utf-8").strip()
        line = "ip rule add " + line + "\n"
        command.append(line)

    command = ''.join(command)
    with open(startup_file, 'w') as file:
        file.write(command)


if __name__ == "__main__":
    save_network_on_file()
