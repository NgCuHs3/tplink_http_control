# tplink_http_control
Yse http protocol to control tp link router.
### This script is simply mac spoofing technique but very effective.
I have 1 tp link load balancer R480T+ connected to the dormitory's LAN with 4 wan ports and a tp router to broadcast the network. This script was written to automatically change the load balancer's MAC address via http protocol (actually at first I didn't know I could use telnet or ssh to connect to the load balancer's cli so I used http indirectly via web interface =))). But http works quite well so I don't want to rewrite the script anymore.
Tools box:
- 1 tp router (AP)
- 1 tp load balancer R480T
- 1 device to run script like lattop or android phone
### Where to find mac address ?
Go around the building and scan the mac address using the Airodump-ng tool on Kali Linux. You will find the right address for spoofing.
