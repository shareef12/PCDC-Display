#!/usr/bin/env python3

"""
AUTHOR: Sam Cappella - sjcappella@gmail.com

Start the Redis server before running this script.
$ redis-server
Default port is 6379
Make sure system can use a lot of memory and enable overcommit_memory
"""

import argparse
import json
import logging
import os
import random
import redis
import sys
import time

import netaddr
from scapy.all import sniff, rdpcap, IP, IPv6, ICMP, TCP, UDP

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BLUE_TEAM_MONIKERS = [
    "Team A",
    "Team B",
    "Team C",
    "Team D",
    "Team E",
    "Team F",
    "Team G",
    "Team H",
]
BLUE_TEAM_RANGES = [
    "10.0.10.0/24",
    "10.0.20.0/24",
    "10.0.30.0/24",
    "10.0.40.0/24",
    "10.0.50.0/24",
    "10.0.60.0/24",
    "10.0.70.0/24",
    "10.0.80.0/24",
]
RED_TEAM_RANGES = [
    "10.2.13.0/16",
    "10.20.17.0/16",
]

BLUE_TEAM_RANGES = [netaddr.IPNetwork(net) for net in BLUE_TEAM_RANGES]
RED_TEAM_RANGES = [netaddr.IPNetwork(net) for net in RED_TEAM_RANGES]

BLUE_TEAM_RANGE_SET = netaddr.IPSet(BLUE_TEAM_RANGES)
RED_TEAM_RANGE_SET = netaddr.IPSet(RED_TEAM_RANGES)

REDIS_PUBSUB_NAME = "ctfview"
PROTOCOLS = {
    0: "DENIAL OF SERVICE",
    20: "FTP",      # FTP Data
    21: "FTP",      # FTP Control
    22: "SSH",
    23: "TELNET",
    25: "EMAIL",    # SMTP
    43: "WHOIS",
    53: "DNS",
    80: "HTTP",
    88: "AUTH",     # Kerberos
    109: "EMAIL",   # POP v2
    110: "EMAIL",   # POP v3
    115: "FTP",     # SFTP
    118: "SQL",
    143: "EMAIL",   # IMAP
    156: "SQL",
    161: "SNMP",
    220: "EMAIL",   # IMAP v3
    389: "AUTH",    # LDAP
    443: "HTTPS",
    445: "SMB",
    636: "AUTH",    # LDAP over SSL/TLS
    1433: "SQL",    # MySQL Server
    1434: "SQL",    # MySQL Monitor
    3306: "SQL",    # MySQL
    3389: "RDP",
    5900: "RDP",    # VNC:0
    5901: "RDP",    # VNC:1
    5902: "RDP",    # VNC:2
    5903: "RDP",    # VNC:3
    8080: "HTTP",   # HTTP Alternative
}

# Global connection to Redis server
redis_server = None

# Statistics to track
packets_sniffed = 0
bytes_sniffed = 0
packets_displayed = 0
bytes_displayed = 0


def test_tcp_udp(test_blue_ips, test_red_ips, iterations):
    logger.info("Running TCP/UDP tests...")
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

        src_port = from_to_ports[0][0]
        dst_port = from_to_ports[1][0]
        proto_name = get_protocol_name(src_port, dst_port)
        from_team = get_team_name(send_receive[0][0])
        to_team = get_team_name(send_receive[1][0])
        size = sizes[0]

        data = {
            "type": "traffic",
            "protocol": proto_name,
            "from": from_team,
            "to": to_team,
            "size": size,
        }
        data = json.dumps(data)
        redis_server.publish(REDIS_PUBSUB_NAME, data)
        time.sleep(0.009)

    logger.info("Finished TCP/UDP tests.")


def test_icmp(test_blue_ips, test_red_ips, iterations):
    logger.info("Running ICMP tests...")
    send_receive = [test_blue_ips, test_red_ips]
    for x in range(0, iterations):
        random.shuffle(test_blue_ips)
        random.shuffle(test_red_ips)
        random.shuffle(send_receive)
        size = 66
        from_team = get_team_name(send_receive[0][0])
        to_team = get_team_name(send_receive[1][0])

        data = {
            "type": "traffic",
            "service": "ICMP",
            "from": from_team,
            "to": to_team,
            "size": size,
        }
        data = json.dumps(data)
        redis_server.publish(REDIS_PUBSUB_NAME, data)
        time.sleep(0.009)
    logger.info("Finished ICMP tests.")


def test_denial_of_service(test_blue_ips, test_red_ips, iterations):
    logger.info("Running Denial of Service tests...")
    for blue_team in test_blue_ips:
        for x in range(0, iterations):
            size = 1
            from_team = get_team_name(test_red_ips[0])
            to_team = get_team_name(blue_team)
            proto_name = "DENIAL OF SERVICE"

            data = {
                "type": "Denial of Service",
                "service": proto_name,
                "from": from_team,
                "to": to_team,
                "size": size,
            }
            data = json.dumps(data)
            redis_server.publish(REDIS_PUBSUB_NAME, data)
    logger.info("Finished Denial of Service tests.")


def test_pwnage(test_blue_ips, test_red_ips, iterations):
    logger.info("Running Pwnage tests...")
    for x in range(0, iterations):
        random.shuffle(test_blue_ips)
        random.shuffle(test_red_ips)
        to_team = get_team_name(test_blue_ips[0])

        data = {
            "type": "pwnage",
            "service": "PWNAGE",
            "from": "Red Team",
            "to": to_team,
            "size": 0,
        }
        data = json.dumps(data)
        redis_server.publish(REDIS_PUBSUB_NAME, data)
        time.sleep(1)
    logger.info("Finished Pwnage tests.")
    pass


def run_tests():
    test_blue_ips = ["10.0.10.1", "10.0.20.1", "10.0.30.1", "10.0.40.1", "10.0.50.1", "10.0.60.1", "10.0.70.1", "10.0.80.1"]
    test_red_ips = ["10.2.13.1", "10.2.13.2", "10.2.13.3", "10.2.13.4", "10.2.17.1", "10.2.17.2", "10.2.17.3", "10.2.17.4"]
    test_tcp_udp(test_blue_ips, test_red_ips, 1000)
    test_icmp(test_blue_ips, test_red_ips, 1000)
    test_pwnage(test_blue_ips, test_red_ips, 15)
    test_denial_of_service(test_blue_ips, test_red_ips, 5000)


def in_range(src_ip, dst_ip):
    """Verify the two IPs are in the correct network ranges.

    Traffic from red -> red is ignored, as well as traffic within a single blue
    team range. Traffic between blue teams is permitted.
    """

    # Ignore traffic between red team networks
    if src_ip in RED_TEAM_RANGE_SET and dst_ip in RED_TEAM_RANGE_SET:
        logger.info("Red Team to Red Team. Drop.")
        return False

    # Ignore traffic within a single blue team network
    for network in BLUE_TEAM_RANGES:
        if src_ip in network and dst_ip in network:
            return False

    if ((src_ip in RED_TEAM_RANGE_SET or src_ip in BLUE_TEAM_RANGE_SET) and
            (dst_ip in RED_TEAM_RANGE_SET or dst_ip in BLUE_TEAM_RANGE_SET)):
        return True

    return False


def get_team_name(ip):
    """Get the team name for an IP address."""
    # Check for Red Team
    if ip in RED_TEAM_RANGE_SET:
        return "Red Team"

    # Check for Blue Team
    for i, network in enumerate(BLUE_TEAM_RANGES):
        if ip in network:
            return BLUE_TEAM_MONIKERS[i]

    logger.warning("Unable to get team name. IP Address: %s", str(ip))
    return ""


def get_protocol_name(src_port, dst_port):
    """Get the service name associated with the given port combination."""
    if src_port in PROTOCOLS:
        return PROTOCOLS[src_port]
    if dst_port in PROTOCOLS:
        return PROTOCOLS[dst_port]
    return ""


def handle_packet(pkt):
    """Callback to process each network packet."""
    global packets_sniffed, bytes_sniffed, packets_displayed, bytes_displayed

    # Update statistics
    packets_sniffed += 1
    bytes_sniffed += len(pkt)

    # IPv6 is not supported
    if IPv6 in pkt:
        return

    try:
        if IP not in pkt:
            return
        src_ip = netaddr.IPAddress(pkt[IP].src)
        dst_ip = netaddr.IPAddress(pkt[IP].dst)

        # Ignore the packet if it isn't between target teams
        if not in_range(src_ip, dst_ip):
            return

        from_team = get_team_name(src_ip)
        to_team = get_team_name(dst_ip)
        if from_team == "" or to_team == "":
            logger.warning("Unable to get team name.")
            return

        # Handle ICMP packets
        if ICMP in pkt:
            msg_type = "traffic"
            service = "ICMP"

        # Handle TCP and UDP packets
        elif TCP in pkt or UDP in pkt:
            src_port = pkt[IP].sport
            dst_port = pkt[IP].dport
            service = get_protocol_name(src_port, dst_port)
            if not service:
                return

            msg_type = "traffic"
            if service == "DENIAL OF SERVICE":
                msg_type = "Denial of Service"
        else:
            return  # Unknown transport protocol

        data = {
            "type": msg_type,
            "service": service,
            "from": from_team,
            "to": to_team,
            "size": len(pkt),
        }
        data = json.dumps(data)
        redis_server.publish(REDIS_PUBSUB_NAME, data)
        packets_displayed += 1
        bytes_displayed += len(pkt)

    except:
        pkt.show()
        logger.exception("Error analyzing packet")


def initialize(randomize):
    """Initialize globals as needed."""
    logger.info("================================================")
    logger.info(time.strftime("%d/%m/%y" + " - " + time.strftime("%H:%M:%S")))
    logger.info("Initializing...")

    # Randomly determine the order of Blue Team monikers
    if randomize:
        random.shuffle(BLUE_TEAM_MONIKERS)
        logger.info("Team Order: " + str(BLUE_TEAM_MONIKERS))


def print_summary():
    logger.info("%d packets sniffed for a total of %d bytes of data.", packets_sniffed, bytes_sniffed)
    logger.info("%d packets sent for display rendering %d bytes of data.", packets_displayed, bytes_displayed)
    logger.info("Server is quitting...")
    logger.info("================================================")


def main():
    global redis_server

    parser = argparse.ArgumentParser(description="Collect and report traffic to a Redis queue for " +
                                                 "visualization.",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-i", "--interface",
                        help="Interface to capture packets on.")
    parser.add_argument("-f", "--file",
                        help="PCAP file to read input from")
    parser.add_argument("-s", "--redis-host", default="localhost",
                        help="Hostname or IP address of the Redis server.")
    parser.add_argument("-r", "--randomize", action="store_true",
                        help="Randomize the Blue Team monikers so Team A on the display " +
                             "isn't guaranteed to be Team 1.")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Run server in verbose mode. Print log messages to stdout" +
                             "Default mode if output file is blank. Both can be turned on.")
    parser.add_argument("-d", "--debug", action="store_true",
                        help="Run in Debug mode. Only execute predefined tests.")

    args = parser.parse_args()

    # Initialize things needed by the server
    initialize(args.randomize)

    # Connect to Redis
    redis_server = redis.StrictRedis(host=args.redis_host, port=6379, db=0)

    # Check to see if run is for testing
    if args.debug:
        logger.info("Running tests...ignoring all other options.")
        run_tests()
        print_summary()
        parser.exit(0)

    if args.interface:
        logger.info("Capturing on %s", args.interface)
        sniff(iface=args.interface, prn=handle_packet, store=0)
    elif args.file:
        if not os.path.isfile(args.file):
            logger.error("Couldn't open PCAP: '%s'.", args.file)
            parser.exit(1)

        pcap = rdpcap(args.file)
        for pkt in pcap:
            handle_packet(pkt)
    else:
        logger.error("Must specify -i or -f option.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_summary()
        sys.exit(0)
