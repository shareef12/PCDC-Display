#!/usr/bin/env python3

"""
pip3 install redis
"""

import argparse
import logging
import json
import random
import redis
import time

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

TEAMS = ["army", "airforce", "observer", "zombie"]
SERVICES = ["shipyard", "plentyofsquids", "race", "navalenc", "squidnotes"]


def test_all(iterations):
    logger.info("Running tests...")
    redis_server = redis.StrictRedis(host="localhost", port=6379, db=0)

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
                    redis_server.publish("a2f-visuals-production", data)
                    time.sleep(0.02)
        time.sleep(3)
    logger.info("Finished tests.")


def main():
    test_all(10)


if __name__ == "__main__":
    main()
