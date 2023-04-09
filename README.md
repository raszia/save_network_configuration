# Save Network Configuration Linux

This script allows you to save your current network configuration, iptables configuration, and DNS configuration to separate files. It's designed to work with most Linux distributions out of the box and requires minimal dependencies.

## Dependencies

- iproute2 package (usually installed by default)
- iptables package (for saving iptables configuration)
- python >= 3

## Features

- Save network configuration, including IP addresses, routes, and rules
- Save iptables configuration
- Save DNS configuration (resolv.conf)
- Exclude connected routes from the output
- Disable DHCP interfaces and routes from the output
- Support for both IPv4 and IPv6 addresses and routes

## Usage

```sh
python save_my_network.py [options]
```

## sudo required if you are not root

Options

    --include-rule-number: Include rule numbers in the output file
    --exclude-connected-routes: Exclude connected routes in the output
    --disable-dhcp-interfaces: Disable interfaces with DHCP in the output file
    --disable-dhcp-routes: Disable routes with DHCP in the output file
    -n, --network: Output filename for network configuration (default: network.sh)
    -i, --iptables: Output filename for iptables configuration (default: iptables.sh)
    -r, --resolv: Output filename for resolv configuration (DNS configuration) (default: resolv.sh)

Example

    python save_my_network.py --exclude-connected-routes --disable-dhcp-interfaces --network my_network.sh --iptables my_iptables.sh --resolv my_resolv.sh

This command will save the network configuration, iptables configuration, and DNS configuration to the files my_network.sh, my_iptables.sh, and my_resolv.sh, respectively. It will exclude connected routes and disable DHCP interfaces from the network configuration.

## License

Broadcastme is released under the MIT License. See `LICENSE` for more information.
