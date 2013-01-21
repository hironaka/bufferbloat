Instructions:
sudo ./run.sh

Max Queue Size: 20 packets
Mean Transfer Time: 3.04112
Standard Deviation: 0.470129541297

Max Queue Size: 100 packets
Mean Transfer Time: 7.64675
Standard Deviation: 0.98010557467

1. 
TCP congestion control algorithm attempts to achieve full utilization of the links by 
increasing the size of the congestion window until a packet is dropped, i.e. the output 
buffer at the bottleneck link is full. In our case, the long lived tcp connection will 
fill the buffer at the switch, regardless of its size. When a new TCP connection is created
to fetch a webpage, its tcp packets are placed at the end of this queue. The longer the
queue, the longer each packet must wait to be routed to the next hop, and the longer the
webpage fetch takes.

2. 
1000 packet max queue size
1500 byte MTU
100 Mb/s drains

1500 * 1000 * 8 / (100 * 10^6) = 0.12 seconds

3.
RTT ~= 6 * QUEUE_SIZE + C
C = Propagation Delay + Packetization Delay ~= 20ms

4.
One way to mitigate buffer bloat would be to differentiate TCP flows based on the 
Differentiated Services flags in the TCP header. This would only mitigate the problem
by using multiple smaller buffers. 

Another way to mitigate the problem is to employ active queue management algorithms. 
These algorithms intelligently choose to preemptively drop or mark packets prior to the 
queue filling up, preventing a long lived TCP flow from blocking other flows.