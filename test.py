#!/usr/bin/env python3

"""
Simulate a data source for the display server.

This script will generate messages for the redis pub/sub queue used by the
display server. Messages will be submitted to the redis server at the specified
address.
"""

import argparse
import logging
import json
import random
import time

import redis

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

REDIS_PUBSUB_NAME = "ctfview"

TEAMS = ["army", "airforce", "observer", "zombie"]
SERVICES = ["shipyard", "plentyofsquids", "race", "navalenc", "squidnotes"]


def test_deterministic(redis_server, iterations):
    """Send the same data repeatedly - useful for debugging."""
    for tick in range(iterations):
        logger.info("Starting round %d", tick)
        data = {
            "service": "shipyard",
            "from": "army",
            "to": "zombie",
            "size": 5,
        }
        data = json.dumps(data)
        redis_server.publish(REDIS_PUBSUB_NAME, data)
        time.sleep(2)


def test_one_source(redis_server, iterations):
    """Provide randomized data for each iteration.

    For each tick, generate traffic from one team for two services. Send this
    traffic to all other teams.
    """
    for tick in range(0, iterations):
        logger.info("Starting round %d", tick)
        from_team = random.choice(TEAMS)
        other_teams = TEAMS.copy()
        other_teams.remove(from_team)
        for service in random.sample(SERVICES, 2):
            for i in range(5):
                for to_team in other_teams:
                    data = {
                        "service": service,
                        "from": from_team,
                        "to": to_team,
                        "size": 5,
                    }
                    data = json.dumps(data)
                    redis_server.publish(REDIS_PUBSUB_NAME, data)
                    time.sleep(0.02)
        time.sleep(3)


def test_all(redis_server, iterations):
    """Provide randomized data for each iteration.

    For each tick, generate traffic from each team for two services. Send this
    traffic to all other teams.
    """
    for tick in range(0, iterations):
        logger.info("Starting round %d", tick)
        for team in TEAMS:
            for service in random.sample(SERVICES, 2):
                other_teams = TEAMS.copy()
                other_teams.remove(team)
                for i in range(5):
                    data = {
                        "service": service,
                        "from": team,
                        "to": random.choice(other_teams),
                        "size": 5,
                    }
                    data = json.dumps(data)
                    redis_server.publish(REDIS_PUBSUB_NAME, data)
                    time.sleep(0.02)
        time.sleep(3)


def main():
    parser = argparse.ArgumentParser(description="Simulate a data source for the display server",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-i", "--iterations", default=100,
                        help="Number of iterations to perform.")
    parser.add_argument("-d", "--deterministic", action="store_true",
                        help="Use a simple deterministic test that provides the " +
                             "same data repeatedly.")
    parser.add_argument("-o", "--onesource", action="store_true",
                        help="Generate traffic from one team per tick.")
    parser.add_argument("-r", "--redis-host", default="localhost",
                        help="Hostname of redis server to connect to.")
    parser.add_argument("-p", "--redis-port", type=int, default=6379,
                        help="Port of redis server to connect to.")

    args = parser.parse_args()

    redis_server = redis.StrictRedis(host=args.redis_host, port=args.redis_port, db=0)

    logger.info("Running tests...")
    if args.deterministic:
        test_deterministic(redis_server, args.iterations)
    elif args.onesource:
        test_one_source(redis_server, args.iterations)
    else:
        test_all(redis_server, args.iterations)
    logger.info("Finished tests.")

if __name__ == "__main__":
    main()
