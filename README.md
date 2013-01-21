bufferbloat
===========

1. TCP congestion control attempts have full utilization of the links by filling the 
increasing the window size additively until a packet is dropped. A packet will not be dropped 
the queue fills up, and a larger. The queue will already be filled up by the first TCP
flow. Any subsequent flow will have to wait on these queues to empty.

2. 1000 max queue size
1500 byte MTU
size in byte = 1500kB
100 Mb/s

1500 * 1000 * 8 / 100 * 10^6

0.12 seconds

3.
RTT = 6 * queuesize

4.
qualtiy of service with multiple queues
active queue management