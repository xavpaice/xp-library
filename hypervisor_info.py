#!/usr/bin/env python3

import openstack


if __name__ == '__main__':

    conn = openstack.connect(cloud='envvars')
    row_format ="{:<24}{:>12}{:>12}"
    print(row_format.format("Name", "Disk GB avail", "MEM avail"))
    for host in conn.compute.hypervisors(details=True):
        print(row_format.format(host.name, host.disk_available, host.memory_free))
