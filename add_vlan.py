#!/usr/bin/env python3

import argparse
from datetime import datetime
import glob
from shutil import copyfile
import subprocess
import sys
import yaml


def parse_args():
    parser = argparse.ArgumentParser(description='Add a new vlan to an existing bond')
    parser.add_argument('--interface', help='Which interface to operate on')
    parser.add_argument('--mtu', default=1500, type=int,
                        help='MTU we want to set the interface to')
    parser.add_argument('--path', default='/etc/netplan', help='Path to netplan config files')
    parser.add_argument('--commit', action='store_true', help='Write the changes to file?')
    parser.add_argument('--vlan', help='Which vlan to add')
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
        cmd = ['grep', args.interface, filename]
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


def main(args):
    """add a vlan to a netplan config

    Limitation: needs the interface only configured in one .yaml, not multiple
    Limitation: only works for interaces in the 'bonds' section
    """
    dateTimeObj = datetime.now()
    timestamp = dateTimeObj.strftime("%d-%m-%Y-%H%M%S")

    print('Making backup with extension {}'.format(timestamp))

    # find the config file with the interface
    process_file = find_netplan_file(args)
    with open(process_file) as netplan_conf:
        netplan_config = yaml.load(netplan_conf)

    if not args.interface and args.vlan:
        print('needs an interface and a vlan supplied')
        sys.exit(1)

    # edit the chosen interface
    bond_vlan = "{}.{}".format(args.interface, args.vlan)
    netplan_config['network']['vlans'][bond_vlan] = {'id': args.vlan,
                                                     'mtu': args.mtu,
                                                     'link': args.interface,
                                                     }

    # write the file
    if args.commit:
        copyfile(process_file, '{}.{}'.format(process_file, timestamp))
        with open(process_file, 'w') as netplan_conf:
            yaml.dump(netplan_config, netplan_conf)
        cmd = ['netplan', 'apply']
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            print('netplan apply failed with {}'.format(e))
            sys.exit(1)


if __name__ == '__main__':
    args = parse_args()
    main(args)
