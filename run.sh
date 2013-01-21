#!/bin/bash

# Note: Mininet must be run as root.  So invoke this shell script
# using sudo.

time=200
bwnet=1.5
# TODO: If you want the RTT to be 20ms what should the delay on each
# link be?  Set this value correctly.
delay=10

iperf_port=5001

for qsize in 20 100; do
    dir=bb-q$qsize

    # Run bufferbloat.py...
		python bufferbloat.py -b 1.5 -D 5 -d $dir -t 200 -q $qsize
		
    # Output graphs...
    python plot_tcpprobe.py -f $dir/cwnd.txt -o cwnd-q$qsize.png -p $iperf_port
    python plot_queue.py -f $dir/q.txt -o buffer-q$qsize.png
    python plot_ping.py -f $dir/ping.txt -o rtt-q$qsize.png
done
