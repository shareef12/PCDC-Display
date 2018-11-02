#!/usr/bin/env python3

"""
AUTHOR: Sam Cappella - sjcappella@gmail.com

pip3 install tornado redis

TODO:
 - check with redis down
 - change circles to missiles
 - slow down missiles

 - tie in with flag submission

 - fix box width
"""

import functools
import json
import logging
import os
import redis
import sys
import threading
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.websocket

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

WIDTH = 1024
HEIGHT = 768

TEAM_WIDTH = 200
TEAM_HEIGHT = 150

LEGEND_WIDTH = WIDTH - 10
LEGEND_HEIGHT = 82

BORDER_BUFFER = 5

TEAM_AREA_HEIGHT = HEIGHT - LEGEND_HEIGHT


TABLE_LOCATIONS = [
    # Army - left
    (BORDER_BUFFER, (TEAM_AREA_HEIGHT / 2) - (TEAM_HEIGHT / 2)),
    # Air Force - right
    (WIDTH - TEAM_WIDTH - BORDER_BUFFER, (TEAM_AREA_HEIGHT / 2) - (TEAM_HEIGHT / 2)),
    # Observer - top middle
    ((WIDTH / 2) - (TEAM_WIDTH / 2), 0 + BORDER_BUFFER),
    # Zombie - bottom middle
    ((WIDTH / 2) - (TEAM_WIDTH / 2), TEAM_AREA_HEIGHT - TEAM_HEIGHT - BORDER_BUFFER),
    # Legend
    (0 + BORDER_BUFFER, HEIGHT - LEGEND_HEIGHT)
]

TEAMS = [
    {"type": "table", "teamname": "Army",      "shorthand": "Army"},
    {"type": "table", "teamname": "Air Force", "shorthand": "Air Force"},
    {"type": "table", "teamname": "Observer",  "shorthand": "Observer"},
    {"type": "table", "teamname": "Zombie",    "shorthand": "Zombie"},
    {"type": "table", "teamname": "Legend",    "shorthand": "Legend"},
]

SERVICE_RGB = {
    "shipyard"      : "#ff00ff",
    "plentyofsquids": "#ed5259",
    "race"          : "#8e7618",
    "navalenc"      : "#f0c391",
    "squidnotes"    : "#e5e5e5",
}

LISTENERS = []


class IndexHandler(tornado.web.RequestHandler):

    def get(self):
        self.render("index.html")


class WebSocketChatHandler(tornado.websocket.WebSocketHandler):

    def open(self):
        print("[*] websocket opened")
        LISTENERS.append(self)

        print("[*] Initializing teams")
        for i, team in enumerate(TEAMS):
            team["x"] = TABLE_LOCATIONS[i][0]
            team["y"] = TABLE_LOCATIONS[i][1]
            self.write_message(json.dumps(team))

    def on_redis_message(self, msg):
        """Handle a message received from Redis."""
        try:
            data = json.loads(msg["data"].decode("ascii"))
        except:
            logger.warn("Data failed to decode: %r")
            return

        service = data["service"]
        tick = data["tick"]
        defender = data["defender"]
        attacker = data["attacker"]
        color = SERVICE_RGB[service]
        size = 5

        msg = {"type": "traffic", "from": defender, "to": attacker, "size": size, "servicergb": color}
        self.write_message(json.dumps(msg))

    def on_close(self):
        print("[*] Closing connection.")
        LISTENERS.remove(self)


def redis_listener(io_loop, pubsub):
    for message in pubsub.listen():
        for element in LISTENERS:
            io_loop.add_callback(functools.partial(element.on_redis_message, message))


def main():
    handlers = [
        ("/", IndexHandler),
        ("/websocket", WebSocketChatHandler),
    ]

    settings = {
        "static_path": os.path.join(os.path.dirname(__file__), "static")
    }

    # Connect to redis and start a thread to dispatch messages
    try:
        r = redis.Redis()
        ps = r.pubsub()
        ps.subscribe("a2f-visuals-production")
    except redis.ConnectionError:
        logger.exception("Unable to connect to Redis!")
        return

    io_loop = tornado.ioloop.IOLoop.instance()
    t = threading.Thread(target=redis_listener, args=(io_loop,ps))
    t.setDaemon(True)
    t.start()

    # Create and start app listening on port 8888
    app = tornado.web.Application(handlers, **settings)
    app.listen(8888)
    print("[*] Waiting on browser connections...")
    io_loop.start()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[*] Server is quitting...")
        sys.exit(0)
