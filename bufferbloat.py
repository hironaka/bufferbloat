#!/usr/bin/python

"CS244 Spring 2013 Assignment 1: Bufferbloat"

from mininet.topo import Topo
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.net import Mininet
from mininet.log import lg, info
from mininet.util import dumpNodeConnections
from mininet.cli import CLI

from subprocess import Popen, PIPE
from time import sleep, time
from multiprocessing import Process
from argparse import ArgumentParser

from monitor import monitor_qlen
import termcolor as T

import sys
import os
import math

import helper

parser = ArgumentParser(description="Bufferbloat tests")
parser.add_argument('--bw-host', '-B',
                    type=float,
                    help="Bandwidth of host links (Mb/s)",
                    default=1000)

parser.add_argument('--bw-net', '-b',
                    type=float,
                    help="Bandwidth of bottleneck (network) link (Mb/s)",
                    required=True)

parser.add_argument('--delay', '-D',
                    type=float,
                    help="Link propagation delay (ms)",
                    required=True)

parser.add_argument('--dir', '-d',
                    help="Directory to store outputs",
                    required=True)

parser.add_argument('--time', '-t',
                    help="Duration (sec) to run the experiment",
                    type=int,
                    default=10)

parser.add_argument('--maxq',
                    type=int,
                    help="Max buffer size of network interface in packets",
                    default=100)

# Linux uses CUBIC-TCP by default that doesn't have the usual sawtooth
# behaviour.  For those who are curious, invoke this script with
# --cong cubic and see what happens...
# sysctl -a | grep cong should list some interesting parameters.
parser.add_argument('--cong',
                    help="Congestion control algorithm to use",
                    default="reno")

# Expt parameters
args = parser.parse_args()

class BBTopo(Topo):
    "Simple topology for bufferbloat experiment."

    def __init__(self, n=2):
        super(BBTopo, self).__init__()

        # Create two hosts.
        host1 = self.addHost('h1')
        host2 = self.addHost('h2')

        # Here I have created a switch.  If you change its name, its
        # interface names will change from s0-eth1 to newname-eth1.
        switch = self.addSwitch('s0')

        # Create link options dictionary.
        linkopts = dict(bw=args.bw_host, 
                        delay='%.1fms' % (args.delay))
                        
        # Add link from host 1 (home computer) to router.
        self.addLink(host1, switch, **linkopts)
        
        # Add link from host 2 to router. Bottleneck link.
        linkopts['bw'] = args.bw_net
        linkopts['max_queue_size'] = args.maxq
        self.addLink(host2, switch, **linkopts)
        return

# Simple wrappers around monitoring utilities.  You are welcome to
# contribute neatly written (using classes) monitoring scripts for
# Mininet!
def start_tcpprobe(outfile="cwnd.txt"):
    os.system("rmmod tcp_probe; modprobe tcp_probe full=1;")
    Popen("cat /proc/net/tcpprobe > %s/%s" % (args.dir, outfile),
          shell=True)

def stop_tcpprobe():
    Popen("killall -9 cat", shell=True).wait()

def start_qmon(iface, interval_sec=0.1, outfile="q.txt"):
    print "Starting qmon..."
    monitor = Process(target=monitor_qlen, args=(iface, interval_sec, outfile))
    monitor.start()
    return monitor

def start_iperf(net):
		# Start iperf server.
    h2 = net.getNodeByName('h2')
    print "Starting iperf server..."
    cmd = "iperf -s -w 16m"
    print cmd
    server = h2.popen(cmd)
    
    # Start the iperf client on h1.  Ensure that you create a
    # long lived TCP flow.
    h1 = net.getNodeByName('h1')
    print "Starting iperf client..."
    cmd = "iperf -c %s -t %d" % (h2.IP(), args.time)
    print cmd
    client = h1.popen(cmd)

def start_webserver(net):
		print "Starting webserver..."
		h1 = net.getNodeByName('h1')
		proc = h1.popen("python http/webserver.py", shell=True)
		sleep(1)
		return [proc]

def start_ping(net, outfile='ping.txt'):
		# Start a ping train from h1 to h2 (or h2 to h1, does it
    # matter?)  Measure RTTs every 0.1 second.  Read the ping man page
    # to see how to do this.
    print "Starting ping train..."
    h1 = net.getNodeByName('h1')
    h2 = net.getNodeByName('h2')
    cmd = "ping -i .1 -w %d %s > %s/%s" % (args.time, h2.IP(), args.dir, outfile)
    print cmd
    ping = h1.popen(cmd, shell=True)

def get_latency_stats(net):
    print "Capturing latency..."
    server = net.getNodeByName('h1')
    client = net.getNodeByName('h2')
    times = []
    start_time = time()
    while True:
        # Calculate the amount of time to transfer webpage.
        cmd = "curl -o index.html -s -w %%{time_total} %s/http/index.html" % (server.IP())
        print cmd
        p = client.popen(cmd, shell=True, stdout=PIPE)
        time_total = float(p.stdout.read())
        times.append(time_total)
        
        # Break out of loop after enough time has elapsed. 
        sleep(5)
        now = time()
        delta = now - start_time
        if delta > args.time:
            break
    
    # Calculate mean and standard deviation of latency.
    mean = helper.avg(times)
    stdev = helper.stdev(times)
    return [mean, stdev]

def bufferbloat():
    if not os.path.exists(args.dir):
        os.makedirs(args.dir)
    os.system("sysctl -w net.ipv4.tcp_congestion_control=%s" % args.cong)
    topo = BBTopo()
    net = Mininet(topo=topo, host=CPULimitedHost, link=TCLink)
    net.start()
    
    # This dumps the topology and how nodes are interconnected through
    # links.
    dumpNodeConnections(net.hosts)
    
    # This performs a basic all pairs ping test.
    net.pingAll()

    # Start all the monitoring processes
    start_tcpprobe("cwnd.txt")

    # Start monitoring the queue sizes.  Since the switch I
    # created is "s0", I monitor one of the interfaces.  Which
    # interface?  The interface numbering starts with 1 and increases.
    # Depending on the order you add links to your network, this
    # number may be 1 or 2.  Ensure you use the correct number.
    qmon = start_qmon(iface='s0-eth2',
                      outfile='%s/q.txt' % (args.dir))

    # Start iperf, webservers, etc.
    start_iperf(net)
    start_ping(net)
    start_webserver(net)

    # TODO: measure the time it takes to complete webpage transfer
    # from h1 to h2 (say) 3 times.  Hint: check what the following
    # command does: curl -o /dev/null -s -w %{time_total} google.com
    # Now use the curl command to fetch webpage from the webserver you
    # spawned on host h1 (not from google!)
    mean, stdev = get_latency_stats(net)
    print "Mean latency: " + str(mean)
    print "Standard deviation of latency: " + str(stdev)

    # Hint: The command below invokes a CLI which you can use to
    # debug.  It allows you to run arbitrary commands inside your
    # emulated hosts h1 and h2.
    # CLI(net)

    stop_tcpprobe()
    qmon.terminate()
    net.stop()
    # Ensure that all processes you create within Mininet are killed.
    # Sometimes they require manual killing.
    Popen("pgrep -f webserver.py | xargs kill -9", shell=True).wait()

if __name__ == "__main__":
    bufferbloat()
