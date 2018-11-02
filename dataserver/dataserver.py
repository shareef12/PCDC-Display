#!/usr/bin/env python

"""
AUTHOR: Sam Cappella - sjcappella@gmail.com
"""

# Imports
import json
import os
import random
import redis
import sys


from netaddr import IPAddress, IPNetwork, IPSet
from optparse import OptionParser
from scapy.all import *
from time import sleep
from time import strftime

# We should start the Redis server if it isn't started already.
# $ redis-server
# Default port is 6379
# Make sure system can use a lot of memory and overcommit_memory

# Variables
redis_ip = None
redis_instance = None

# File to log data
log_file = "./data_server.out"

blueteam_monikers = ["Team A", "Team B", "Team C", "Team D", "Team E", "Team F", "Team G", "Team H"]

blueteam_ranges = ["10.0.10.0/24", "10.0.20.0/24", "10.0.30.0/24", "10.0.40.0/24", "10.0.50.0/24", "10.0.60.0/24", "10.0.70.0/24", "10.0.80.0/24"]
# For testing
#blueteam_ranges = ["192.168.1.1/32", "192.168.1.5/32", "192.168.1.7/32", "192.168.1.6/32", "192.168.1.8/32", "24.214.95.0/24", "198.41.208.0/24", "63.245.215.0/24"]

redteam_ranges = ["10.2.13.0/16", "10.20.17.0/16"]
# For testing
#redteam_ranges = ["192.168.1.2/32"]

# Stats to track
packets_sniffed = 0
bytes_sniffed = 0
packets_displayed = 0
bytes_displayed = 0

# Simple log function
def log(string, log_type=""):
    global log_file
    if log_type == "":
        log_type = "INFO" 
    with open(log_file,"a+") as f:
        f.write("[ " + log_type + " ] " + string + "\n")
        f.close()
    # Types: ERROR, WARNING, CRITICAL WARNING, STARTUP, SHUTDOWN
    print("[ " + log_type + " ] " + str(string))

# Test TCP/UDP traffic
def test_tcp_udp(test_blue_ips, test_red_ips, iterations):
    log("Running TCP/UDP tests...")
    send_receive = [test_blue_ips, test_red_ips]
    test_ports = [20, 21, 22, 23, 25, 43, 53, 80, 88, 109, 110, 115, 118, 143, 156, 161, 220, 389, 443, 445, 636, 1433, 1434, 3306, 3389, 5900, 5901, 5902, 5903, 8080]
    from_to_ports = [test_ports, [1337]]
    sizes = [66, 74, 87, 104, 107, 111, 113, 123, 131, 156, 222, 308, 475, 492, 583, 1218, 1374, 1466, 2866, 2902]
    for x in range(0, iterations):
        random.shuffle(test_blue_ips)
        random.shuffle(test_red_ips)
        random.shuffle(send_receive)
        random.shuffle(test_ports)
        random.shuffle(from_to_ports)
        random.shuffle(sizes)

        msg_type = "Traffic"
        size = sizes[0]
        from_team = get_team_name(send_receive[0][0])
        to_team = get_team_name(send_receive[1][0])
        src_ip = send_receive[0][0]
        dst_ip = send_receive[1][0]
        src_port = from_to_ports[0][0]
        dst_port = from_to_ports[1][0]
        proto_name = get_tcp_udp_proto(src_port, dst_port)

        data = dict({
                     "type": msg_type,
                     "size": size,
                     "from": from_team,
                     "to": to_team,
                     "src_ip": src_ip,
                     "dst_ip": dst_ip,
                     "src_port": src_port,
                     "dst_port": dst_port,
                     "protocol": proto_name
            })
        data = json.dumps(data)
        redis_instance.publish("pcdc-visuals-production", data)
        sleep(0.009)

    log("Finished TCP/UDP tests.")

# Test ICMP traffic
def test_icmp(test_blue_ips, test_red_ips, iterations):
    log("Running ICMP tests...")
    send_receive = [test_blue_ips, test_red_ips]
    for x in range(0, iterations):
        random.shuffle(test_blue_ips)
        random.shuffle(test_red_ips)
        random.shuffle(send_receive)

        msg_type = "Traffic"
        size = 66
        from_team = get_team_name(send_receive[0][0])
        to_team = get_team_name(send_receive[1][0])
        src_ip = send_receive[0][0]
        dst_ip = send_receive[1][0]
        src_port = 0
        dst_port = 0
        proto_name = "ICMP"

        data = dict({
                     "type": msg_type,
                     "size": size,
                     "from": from_team,
                     "to": to_team,
                     "src_ip": src_ip,
                     "dst_ip": dst_ip,
                     "src_port": src_port,
                     "dst_port": dst_port,
                     "protocol": proto_name
            })
        data = json.dumps(data)
        redis_instance.publish("pcdc-visuals-production", data)
        sleep(0.009)
    log("Finished ICMP tests.")


# Test Denial of Service
def test_denial_of_service(test_blue_ips, test_red_ips, iterations):
    log("Running Denial of Service tests...")
    for blue_team in test_blue_ips:
        for x in range(0, iterations):
            msg_type = "Denial of Service"
            size = 1
            from_team = get_team_name(test_red_ips[0])
            to_team = get_team_name(blue_team)
            src_ip = test_red_ips[0]
            dst_ip = blue_team
            src_port = 1337
            dst_port = 0
            proto_name = "DENIAL OF SERVICE"

            data = dict({
                         "type": msg_type,
                         "size": size,
                         "from": from_team,
                         "to": to_team,
                         "src_ip": src_ip,
                         "dst_ip": dst_ip,
                         "src_port": src_port,
                         "dst_port": dst_port,
                         "protocol": proto_name
                })
            data = json.dumps(data)
            redis_instance.publish("pcdc-visuals-production", data)
    log("Finished Denial of Service tests.")

# Test Pwnage
def test_pwnage(test_blue_ips, test_red_ips, iterations):
    log("Running Pwnage tests...")
    for x in range(0, iterations):
        random.shuffle(test_blue_ips)
        random.shuffle(test_red_ips)


        to_team = get_team_name(test_blue_ips[0])

        data = dict({
                     "type": "Pwnage",
                     "size": 0,
                     "from": "Red Team",
                     "to": to_team,
                     "src_ip": test_blue_ips[0],
                     "dst_ip": test_red_ips[0],
                     "src_port": 35555,
                     "dst_port": 4444,
                     "protocol": "PWNAGE"
            })
        data = json.dumps(data)
        redis_instance.publish("pcdc-visuals-production", data)
        sleep(1)

    log("Finished Pwnage tests.")
    pass

# Test function to debug functionality
def run_tests():
    test_blue_ips = ["10.0.10.1", "10.0.20.1", "10.0.30.1", "10.0.40.1", "10.0.50.1", "10.0.60.1", "10.0.70.1", "10.0.80.1"]
    test_red_ips = ["10.2.13.1", "10.2.13.2", "10.2.13.3", "10.2.13.4", "10.2.17.1", "10.2.17.2", "10.2.17.3", "10.2.17.4"]
    test_tcp_udp(test_blue_ips, test_red_ips, 1000)
    test_icmp(test_blue_ips, test_red_ips, 1000)
    test_pwnage(test_blue_ips, test_red_ips, 15)
    test_denial_of_service(test_blue_ips, test_red_ips, 5000)


# Check to see if 2 IP addresses are interesting
def in_range(src_ip, dst_ip):
    src_in_range = False
    dst_in_range = False

    # Check to make sure they both aren't in the Red Team range
    if IPAddress(src_ip) in IPSet(redteam_ranges) and IPAddress(dst_ip) in IPSet(redteam_ranges):
        log("Red Team to Red Team. Drop.", "WARNING")
        return False
    
    # Check to see if IP addresses belong to the same Blue Team
    # NOTE: IF you are testing this on your LAN and your 'Red Team' is in the same /24 as your 'Blue Teams', 
    # you will not see any traffic. Comment this out if that is your case.
    if IPNetwork(src_ip + "/24") == IPNetwork(dst_ip + "/24"):
        return False

    # Check to make sure they both aren't in the Blue Team range
    if IPAddress(src_ip) in IPSet(blueteam_ranges) and IPAddress(dst_ip) in IPSet(blueteam_ranges):
        log("Blue Team to Blue Team!!!", "CRITICAL-WARNING")
        log(str(src_ip) + " --> " + str(dst_ip), "CRITICAL-WARNING")
        return False

    # Check to see if source IP is from Red Team
    if IPAddress(src_ip) in IPSet(redteam_ranges):
        src_in_range = True
    
    # Check to see if source IP is from Blue Team
    if src_in_range is False:
        if IPAddress(src_ip) in IPSet(blueteam_ranges):
            src_in_range = True

    # Check to see if destination IP is to Red Team
    if IPAddress(dst_ip) in IPSet(redteam_ranges):
        dst_in_range = True
    
    # Check to see if destination IP is to Blue Team
    if dst_in_range is False:
        if IPAddress(dst_ip) in IPSet(blueteam_ranges):
            dst_in_range = True
    
    # Return True if we have 2 interesting IPs in the correct ranges
    return src_in_range & dst_in_range

# Get the team name for the specified IP address
def get_team_name(ip_addr):
    # Check for Red Team
    if IPAddress(ip_addr) in IPSet(redteam_ranges):
        return "Red Team"

    # Check for Blue Team
    index = 0
    for blueteam_range in blueteam_ranges:
        if IPAddress(ip_addr) in IPNetwork(blueteam_range):
            return blueteam_monikers[index]
        else:
            index += 1
    log("Error getting team name. IP Address: " + str(ip_addr), "ERROR")
    return ""

# Check to see if packet is using an interesting TCP/UDP protocol based on source or destination port
def get_tcp_udp_proto(src_port, dst_port):
    if dst_port == 0:                           # Denial of Service
        return "DENIAL OF SERVICE"      
    if dst_port == 20 or src_port == 20:        # FTP Data
        return "FTP"
    if dst_port == 21 or src_port == 21:        # FTP Control
        return "FTP"
    if dst_port == 22 or src_port == 22:        # SSH
        return "SSH"
    if dst_port == 23 or src_port == 23:        # Telnet
        return "TELNET"
    if dst_port == 25 or src_port == 25:        # SMTP
        return "EMAIL"
    if dst_port == 43 or src_port == 43:        # Whois
        return "WHOIS"
    if dst_port == 53 or src_port == 53:        # DNS
        return "DNS"
    if dst_port == 80 or src_port == 80:        # HTTP
        return "HTTP"
    if dst_port == 88 or src_port == 88:        # Kerberos
        return "AUTH"
    if dst_port == 109 or src_port == 109:      # POP v2
        return "EMAIL"
    if dst_port == 110 or src_port == 110:      # POP v3
        return "EMAIL"
    if dst_port == 115 or src_port == 115:      # SFTP
        return "FTP"
    if dst_port == 118 or src_port == 118:      # SQL
        return "SQL"
    if dst_port == 143 or src_port == 143:      # IMAP
        return "EMAIL"
    if dst_port == 156 or src_port == 156:      # SQL
        return "SQL"
    if dst_port == 161 or src_port == 161:      # SNMP
        return "SNMP"
    if dst_port == 220 or src_port == 220:      # IMAP v3
        return "EMAIL"
    if dst_port == 389 or src_port == 389:      # LDAP
        return "AUTH"
    if dst_port == 443 or src_port == 443:      # HTTPS
        return "HTTPS"
    if dst_port == 445 or src_port == 445:      # SMB
        return "SMB"
    if dst_port == 636 or src_port == 636:      # LDAP of SSL/TLS
        return "AUTH"
    if dst_port == 1433 or src_port == 1433:    # MySQL Server
        return "SQL"
    if dst_port == 1434 or src_port == 1434:    # MySQL Monitor
        return "SQL"
    if dst_port == 3306 or src_port == 3306:    # MySQL
        return "SQL"
    if dst_port == 3389 or src_port == 3389:    # RDP
        return "RDP"
    if dst_port == 5900 or src_port == 5900:    # VNC:0
        return "RDP"
    if dst_port == 5901 or src_port == 5901:    # VNC:1
        return "RDP"
    if dst_port == 5902 or src_port == 5902:    # VNC:2
        return "RDP"
    if dst_port == 5903 or src_port == 5903:    # VNC:3
        return "RDP"
    if dst_port == 8080 or src_port == 8080:    # HTTP Alternative
        return "HTTP"

    return ""

# Function call back for each packet
def pkt_callback(pkt):
    global packets_sniffed, bytes_sniffed, packets_displayed, bytes_displayed
    # Add to stats
    packets_sniffed += 1
    bytes_sniffed += len(pkt)

    # Check for IPv6, currently no support
    if IPv6 in pkt:
        return
    # Wrap everything in a try, prevent crash
    try:
        # Check for TCP or UDP packet
        if TCP in pkt or UDP in pkt:
            # Need to check for an IP layer
            if IP not in pkt:
                return;
            src_ip = pkt[IP].src
            dst_ip = pkt[IP].dst
            # Check to make sure IP addresses are in range
            if in_range(src_ip, dst_ip):
                src_port = pkt[IP].sport
                dst_port = pkt[IP].dport
                # Check to make sure it is a protocal to visualize
                proto_name = get_tcp_udp_proto(src_port, dst_port)
                if proto_name == "":
                    return
                from_team = get_team_name(src_ip)
                to_team = get_team_name(dst_ip)
                if from_team == "" or to_team == "":
                    log("Error creating TCP/UDP message.", "ERROR")
                    return
                msg_type = ""
                if proto_name == "DENIAL OF SERVICE":
                    msg_type = "Denial of Service"
                else:
                    msg_type = "Traffic"
                data = dict({
                            "type": msg_type, 
                            "size": len(pkt),
                            "from":from_team, 
                            "to": to_team, 
                            "src_ip": src_ip, 
                            "dst_ip": dst_ip, 
                            "src_port": src_port, 
                            "dst_port": dst_port, 
                            "protocol": proto_name
                             })
                data = json.dumps(data)
                redis_instance.publish("pcdc-visuals-production", data)
                packets_displayed += 1
                bytes_displayed += len(pkt)
                return
                
        # Check for ICMP
        if ICMP in pkt:
            # Need to check for an IP layer
            if IP not in pkt:
                return
            src_ip = pkt[IP].src
            dst_ip = pkt[IP].dst
            # Make sure it is in range
            if in_range(src_ip, dst_ip):
                from_team = get_team_name(src_ip)
                to_team = get_team_name(dst_ip)
                if from_team == "" or to_team == "":
                    log("Error creating ICMP message.", "ERROR")
                    return
                data = dict({
                            "type": "Traffic",
                            "size": len(pkt), 
                            "from": from_team, 
                            "to": to_team, 
                            "src_ip": src_ip, 
                            "dst_ip": dst_ip,
                            "src_port": "0",
                            "dst_port": "0", 
                            "protocol":"ICMP" })
                data = json.dumps(data)
                redis_instance.publish("pcdc-visuals-production", data)
                packets_displayed += 1
                bytes_displayed += len(pkt)
                return

    except Exception as e:
        pkt.show()
        log("Error analyzing packet: " + str(e), "ERROR")
    
       
# Function to start and connect to redis
def connect_redis():
    r = redis.StrictRedis(host=redis_ip, port=6379, db=0)
    return r

# Function to initialize settings
def initialize(randomize):
    # Consider starting REDIS server...get feedback.
    log("================================================", "STARTUP")
    log(strftime("%d/%m/%y" + " - " + strftime("%H:%M:%S")))
    log("Initializing...")
    global log_file
    if log_file != "./data_server.out":
        log("Logging output to: " + log_file)
    else:
        log("No log file output provided.")
        log("Defaulting to: " + log_file)

    # Randomly determine the order of Blue Team monikers
    if randomize == True:
        random.shuffle(blueteam_monikers)
        log("Team Order: " + str(blueteam_monikers))

# Define the shutdown function
def shutdown():
    global packets_sniffed, packets_displayed, bytes_sniffed, bytes_displayed
    log(str(packets_sniffed) + " packets sniffed for a total of " + str(bytes_sniffed) + " bytes of data.")
    log(str(packets_displayed) + " packets sent for display rendering " + str(bytes_displayed) + " bytes of data.")
    log("Server is quitting...", "SHUTDOWN")
    log("================================================", "SHUTDOWN")

# Define main function
def main(argv):
    global redis_instance, redis_ip, log_file
    if os.getuid() != 0:
        print("Please run this script as ROOT or with SUDO.")
        print("Quitting.")
        sys.exit()
    # Create option parser
    parser = OptionParser()
    # Define command line arguments
    parser.add_option("-d", "--debug", action="store_true", dest="debug_mode", help="Run in Debug mode. Only predefined tests will be run.\n")
    parser.add_option("-i", "--interface", dest="interface", help="Interface to receive packets on.\n")
    parser.add_option("-m", "--read-me", action="store_true", dest="show_readme", help="Show legal and readme information.\n")
    parser.add_option("-v", "--verbose", action="store_true", dest="verbose", help="Run server in verbose mode. Print to STDOUT. Default mode if output file is blank. Both can be turned on.\n")
    parser.add_option("-f", "--file", dest="pcap_file", help="File if reading from a PCAP file.\n")
    parser.add_option("-o", "--output", dest="output", help="File to write the logs to.\n")
    parser.add_option("-r", "--random", action="store_true", dest="randomize", help="Randomize the Blue Team monikors so Team A on the display isn't garaunteed to be Team 1.\n")
    parser.add_option("-s", "--redis-server-ip", dest="redis_ip", help="IP address of the REDIS server.\n")
    (options, args) = parser.parse_args()

    if options.output is not None:
        log_file = options.output
    # Initialize things needed by the server
    initialize(options.randomize)

    # Parse command line arguments
    if options.show_readme == True:
        print("README:")
        print("This is the data server component of a realtime network visualization built for cyber defense competitions.")
        print("If you encounter any issues, errors, bugs, or want additional features, please contact the original auther.")
        print("Author: Sam Cappella - sjcappella@gmail.com")
        print("Link: https://github.com/sjcappella/PCDC-Display")
        sys.exit()
    # Connect to Redis
    if options.redis_ip == None:
        log("No IP address specified for REDIS server. Defaulting to LocalHost.")
        redis_ip = "127.0.0.1"
        redis_instance = connect_redis()
    else:
        redis_ip = options.redis_ip
        redis_instance = connect_redis()
    # Check to see if run is for testing
    if options.debug_mode is True:
        log("Running tests...ignoring all other options.")
        run_tests()
        shutdown()
        sys.exit()
    if options.interface == None:
        log("No interface specified. Defaulting to PCAP.")
        if options.pcap_file == None:
            log("No PCAP specified. Quitting!")
            sys.exit()
        elif os.path.exists(options.pcap_file) == False:
            log("Couldn't find PCAP. Quitting!")
            sys.exit()
        else:
            pcap = rdpcap(options.pcap_file)
            for pkt in pcap:
                pkt_callback(pkt)
    else:
        log("Sniffing on " + str(options.interface))
        sniff(iface=options.interface, prn=pkt_callback, store=0)


# Call main function on entry
if __name__ == "__main__":
    # Wrap main() in keyboard interrupt
    try:
        main(sys.argv)
    except KeyboardInterrupt:
        shutdown()
        sys.exit(0)
