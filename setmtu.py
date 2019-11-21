#!/usr/bin/env python3

import argparse
from datetime import datetime
import glob
import shlex
from shutil import copyfile
import subprocess
import sys
import yaml


def parse_args():
    parser = argparse.ArgumentParser(description='Summarize hypervisor memory and cpu usage.')
    parser.add_argument('--interface', help='Which interface to operate on')
    parser.add_argument('--mtu', default=9000, type=int,
                        help='MTU we want to set the interface to')
    parser.add_argument('--path', default='/etc/netplan', help='Path to netplan config files')
    parser.add_argument('--commit', action='store_true', help='Write the changes to file?')
    parser.add_argument('--subnet', help='Which subnet to operate on, use an expression suitable for grep.'
                        ' Lower priority than the --interface arg.')
    args = parser.parse_args()
    return args


def find_netplan_file(args):
    """Loop through all the netplan files, looking for the first one
    with the required interface.  Returns a dict wtih the config, plus an interface name.

    Will only read one file, if the interface is defined in more than one file
    the config is broken and we need to fix that.
    """

    file_list = [f for f in glob.glob(args.path + '/*.yaml')]
    selected_files = []
    for filename in file_list:
        if args.interface:
            cmd = ['grep', args.interface, filename]
        elif args.subnet:
            cmd = ['grep', args.subnet, filename]
        else:
            print("must set either --interface or --subnet")
            sys.exit(1)
        try:
            result = subprocess.run(cmd, check=True)
            if result.returncode == 0:
                selected_files.append(filename)
        except subprocess.CalledProcessError:
            continue

    if len(selected_files) > 1:
        # broken
        print("more than one file has this interface defined")
        sys.exit(1)
    elif len(selected_files) == 0:
        print("Interface was not found in {}".format(args.path))
        sys.exit(1)
    if len(selected_files) == 1:
        return selected_files[0]
    return False


def get_interface_from_subnet(data):
    interface = False
    if args.subnet:
        # stand by for some nesting
        # mutliple types of interfaces
        interface_types = [t for t in data['network'].keys() if t != 'version']
        for interface_type in interface_types:
            interfaces = [i for i in data['network'][interface_type].keys()]
            int_with_address = [i for i in interfaces if data['network'][interface_type][i].get('addresses')]
            for this_interface in int_with_address:
                for address in data['network'][interface_type][this_interface]['addresses']:
                    if address.find(args.subnet):
                        return this_interface, interface_type
    return False


def change_interface(interface, mtu, commit):
        cmd = 'ip link set dev {} mtu {}'.format(interface, mtu)
        print(cmd)
        # TODO exception handling
        if commit:
            result = subprocess.run(shlex.split(cmd), shell=True)
            if result.returncode == 0:
                print("MTU changed successfully for {}".format(interface))
            else:
                print("MTU change failed for {}".format(interface))


def main(args):
    """Change the MTU on the running interfaces and netplan config file.

    Limitation: needs the interface only configured in one .yaml, not multiple
    Limitation: only supports supplied interface if it's a vlan interface
    """
    dateTimeObj = datetime.now()
    timestamp = dateTimeObj.strftime("%d-%m-%Y-%H%M%S")

    print('Making backup with extension {}'.format(timestamp))

    # find the config file with the interface
    process_file = find_netplan_file(args)
    with open(process_file) as netplan_conf:
        netplan_config = yaml.load(netplan_conf)
    if args.interface:
        interface = args.interface
        interface_type = 'vlans'  # quick and dirty
    else:
        interface, interface_type = get_interface_from_subnet(netplan_config)

    # TODO make this smarter, currently only support vlans
    # edit the chosen interface
    netplan_config['network'][interface_type][interface]['mtu'] = args.mtu
    change_interface(interface, args.mtu, args.commit)

    # if there's a bridge, edit that
    # only operates if the chosen interface is a vlan
    bridges_tofix = []
    if 'bridges' in netplan_config['network'].keys() and interface_type == 'vlans':
        for bridge in netplan_config['network']['bridges'].keys():
            if args.interface in netplan_config['network']['bridges'][bridge]['interfaces']:
                bridges_tofix.append(bridge)
    for bridge in bridges_tofix:
        netplan_config['network']['bridges'][bridge]['mtu'] = args.mtu
        change_interface(bridge, args.mtu, args.commit)
        path = '/sys/devices/virtual/net/' + bridge + '/lower_'
        subinterfaces = [f.replace(path, '') for f in glob.glob(path + '*')]
        for subinterface in subinterfaces:
            if subinterface == interface:
                continue
            change_interface(subinterface, args.mtu, args.commit)

    # write the file
    if args.commit:
        copyfile(process_file, '{}.{}'.format(process_file, timestamp))
        with open(process_file, 'w') as netplan_conf:
            yaml.dump(netplan_config, netplan_conf)


if __name__ == '__main__':
    args = parse_args()
    main(args)
