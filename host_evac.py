#!/usr/bin/env python3

import argparse
import openstack
from time import sleep


def parse_args():
    parser = argparse.ArgumentParser(description='Evacuate a hypervisor')
    parser.add_argument('--host', help='host to evacuate')
    args = parser.parse_args()
    return args


def hypervisor_has_servers(conn, hypervisor):
    servers = conn.compute.servers(all_projects=True, host=hypervisor)
    if len(list(servers)) > 0:
        return True
    return False


def wait_for_all_active(conn, hypervisor):
    # loop while servers are migrating
    for loops in range(1, 50):
        wait = False
        servers = conn.compute.servers(details=True, all_projects=True, host=hypervisor)

        for server in servers:
            if not server.status == 'ACTIVE':
                wait = True
        if wait:
            sleep(30)
        else:
            break
    if loops > 40:
        raise Exception("Looped too many times waiting for all instances on the host to be active")


def main(conn, hypervisor):

    if hypervisor_has_servers(conn, hypervisor):
        for server in conn.compute.servers(details=True, all_projects=True, host=hypervisor):
            wait_for_all_active(conn, hypervisor)
            conn.compute.live_migrate_server(server, block_migration=True)


if __name__ == '__main__':

    conn = openstack.connect(cloud='envvars')
    args = parse_args()
    main(conn, args.host)
