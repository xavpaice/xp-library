# first arg is IP of VM reachable from router
# second is the neutron-gateway unit name
# third is the router ID
ssh ubuntu@$1 -o ProxyCommand="juju ssh $2 sudo ip netns exec qrouter-$3 nc %h %p"
