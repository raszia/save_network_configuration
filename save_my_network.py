# #!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import shlex
import argparse
import sys
from subprocess import Popen, PIPE


class Result:
    pass


def run_command_no_error(command):
    result = Result()

    p = Popen(shlex.split(command), stdin=PIPE, stdout=PIPE, stderr=PIPE)
    (stdout, stderr) = p.communicate()

    result.exit_code = p.returncode
    result.stdout = stdout
    result.stderr = stderr
    result.command = command

    return result


def check_command_exists(command):
    try:
        Popen([command], stdout=PIPE, stderr=PIPE)
    except FileNotFoundError:
        return False
    return True


def get_indexes(value, lst):
    return [i for (elem, i) in zip(lst, range(len(lst))) if value == elem]


def is_dhcp_interface(interface):
    ip_output = run_command_no_error(
        f"ip -4 -o addr show {interface}").stdout.decode("utf-8")
    return "dynamic" in ip_output


def get_dynamic_interfaces(interfaces):
    return {interface for interface in interfaces if is_dhcp_interface(interface)}


def append_ip_addresses(commands, interface, ip_address):
    inet_numbers = get_indexes(b"inet", ip_address)

    for inet in inet_numbers:
        ip_address_elemnt = inet + 1
        ip_prefix = ip_address[ip_address_elemnt]
        single_command = f"ip addr add {ip_prefix.decode('utf-8')} dev {interface}\n"
        commands.append(single_command)


def append_interface_flags(commands, interface):
    with open(f"/sys/class/net/{interface}/flags", "r") as flags_file:
        flags = flags_file.read().strip()
    commands.append(f"echo {flags} > /sys/class/net/{interface}/flags\n")


def append_routes(commands, route_lines, dynamic_interfaces):
    for line in route_lines:
        line_str = line.decode("utf-8").strip()
        if DISABLE_DHCP_ROUTES and "dhcp" in line_str:
            continue
        # Exclude connected routes
        if EXCLUDE_CONNECTED_ROUTES and ("link" in line_str or "proto kernel" in line_str):
            continue

        if DISABLE_DHCP_INTERFACES:
            route_interface = line_str.split()[-1]
            if route_interface in dynamic_interfaces:
                continue
        commands.append(f"ip route add {line.decode('utf-8')}\n")


def append_rules(commands, rule_lines):
    for line in rule_lines:
        line_str = line.decode("utf-8").strip()
        if not INCLUDE_RULE_NUMBER:
            line_str = line_str.split(':')[1].strip()
        commands.append(f"ip rule add {line_str}\n")


def save_network_config_to_file(filename='network.sh'):
    command = "ip"
    if not check_command_exists(command):
        print("Error: 'ip' command not found. Please ensure you have the 'iproute2' package installed.")
        return
    interfaces = os.listdir('/sys/class/net/')
    commands = ["#!/bin/bash\n"]
    dynamic_interfaces = get_dynamic_interfaces(
        interfaces) if DISABLE_DHCP_INTERFACES else set()

    for interface in interfaces:
        if interface in dynamic_interfaces:
            continue

        # Save IPv4 and IPv6 addresses
        for ip_version in ['-4', '-6']:
            ip_output = run_command_no_error(
                f"ip {ip_version} -o addr show {interface}")
            ip_address = ip_output.stdout.split()
            append_ip_addresses(commands, interface, ip_address)

        append_interface_flags(commands, interface)

    # Save IPv4 and IPv6 routes
    for ip_version in ['-4', '-6']:
        route_output = run_command_no_error(f"ip {ip_version} route list")
        route_lines = route_output.stdout.splitlines()
        append_routes(commands, route_lines, dynamic_interfaces)

    rule = run_command_no_error("ip rule list")
    rule_lines = rule.stdout.splitlines()
    append_rules(commands, rule_lines)

    with open(filename, 'w') as file:
        file.writelines(commands)
    print(f"Network configuration saved to {filename}")


def save_iptables_to_file(filename='iptables.sh'):
    command = "iptables-save"
    if not check_command_exists(command):
        print("Error: 'iptables-save' command not found. Please ensure you have the 'iptables' package installed.")
        return

    iptables_config = run_command_no_error(command).stdout.decode('utf-8')
    iptables_lines = iptables_config.splitlines()

    iptables_commands = ["#!/bin/bash\n"]

    table = ""
    for line in iptables_lines:
        if line.startswith("#") or not line:
            continue
        if line.startswith("*"):
            table = line[1:]
        elif line.startswith(":"):
            chain, policy, counters = line[1:].split(" ", 2)
            iptables_commands.append(
                f"iptables -t {table} -P {chain} {policy}\n")
        elif line.startswith("-"):
            iptables_commands.append(f"iptables {line}\n")

    with open(filename, 'w') as file:
        file.writelines(iptables_commands)
    print(f"iptables configuration saved to {filename}")


def save_dns_config_to_file(filename='dns_config.sh'):
    source_file = '/etc/resolv.conf'

    try:
        with open(source_file, 'r') as file:
            lines = file.readlines()

        with open(filename, 'w') as file:
            file.write("#!/bin/bash\n")
            file.write("cat << 'EOF' > /etc/resolv.conf\n")
            for line in lines:
                file.write(line)
            file.write("EOF\n")

        print(f"DNS configuration saved to {filename}")

    except IOError as e:
        print(f"Error: Failed to save DNS configuration: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Save network configuration to a file.')
    parser.add_argument('--include-rule-number', dest='include_rule_number', action='store_true',
                        help='Include rule numbers in the output file')
    parser.add_argument('--exclude-connected-routes', action='store_true',
                        help='Exclude connected routes in the output')
    parser.add_argument('--disable-dhcp-interfaces', dest='disable_dhcp_interfaces', action='store_true',
                        help='Disable interfaces with DHCP in the output file')
    parser.add_argument('--disable-dhcp-routes', dest='disable_dhcp_routes', action='store_true',
                        help='Disable routes with DHCP in the output file')
    parser.add_argument('-n', '--network', default='network.sh',
                        help='Output filename (default: network.sh)')
    parser.add_argument('-i', '--iptables', default='iptables.sh',
                        help='Output filename for iptables config (default: iptables.sh)')
    parser.add_argument('-r', '--resolv', default='resolv.sh',
                        help='Output filename for resolv config (dns config) (default: resolv.sh)')
    args = parser.parse_args()

    INCLUDE_RULE_NUMBER = args.include_rule_number
    DISABLE_DHCP_INTERFACES = args.disable_dhcp_interfaces
    DISABLE_DHCP_ROUTES = args.disable_dhcp_routes
    EXCLUDE_CONNECTED_ROUTES = args.exclude_connected_routes

    save_iptables_to_file(args.iptables)
    save_network_config_to_file(args.network)
    save_dns_config_to_file(args.resolv)
