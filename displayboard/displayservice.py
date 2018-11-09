#!/usr/bin/env python3

"""
AUTHOR: Sam Cappella - sjcappella@gmail.com

pip3 install tornado redis
"""

import datetime
import json
import logging
import os
import sys
import threading

import redis
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.websocket

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DELAY_SECONDS = 1

TEAMS = [
    {"name": "army",     "display_name": "Army",      "location": "left",   "color": "Olive"},
    {"name": "airforce", "display_name": "Air Force", "location": "right",  "color": "Blue"},
    {"name": "observer", "display_name": "Observer",  "location": "top",    "color": "Red"},
    {"name": "zombie",   "display_name": "Zombie",    "location": "bottom", "color": "DimGray"},
]

#for t in TEAMS: t["color"] = "blue"

SERVICES = [
    {"name": "shipyard",       "color": "#ff00ff"},
    {"name": "plentyofsquids", "color": "#ed5259"},
    {"name": "race",           "color": "#40e0d0"},
    {"name": "navalenc",       "color": "#f0c391"},
    {"name": "squidnotes",     "color": "#00ff00"},
]
SERVICE_RGB = {s["name"]: s["color"] for s in SERVICES}

LISTENERS = []


class IndexHandler(tornado.web.RequestHandler):

    def get(self):
        self.render("index.html")


class WebSocketChatHandler(tornado.websocket.WebSocketHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, *kwargs)
        self.timeouts = []

    def open(self):
        print("[*] websocket opened")
        LISTENERS.append(self)

        print("[*] Initializing legend")
        msg = {"type": "legend", "services": SERVICES}
        self.write_message(json.dumps(msg))

        print("[*] Initializing teams")
        msg = {"type": "teams", "teams": TEAMS}
        self.write_message(json.dumps(msg))

    def on_redis_message(self, msg):
        """Handle a message received from Redis."""
        # TODO: Ensure we're removing the right element and we don't have leaks
        self.timeouts = self.timeouts[1:]

        try:
            data = json.loads(msg["data"].decode("ascii"))
        except:
            logger.warn("Data failed to decode: %r")
            return

        service = data["service"]
        from_team = data["from"]
        to_team = data["to"]
        size = data["size"]
        color = SERVICE_RGB[service]

        msg = {"type": "traffic", "from": from_team, "to": to_team, "size": size, "color": color}
        self.write_message(json.dumps(msg))

    def on_close(self):
        print("[*] Closing connection.")
        LISTENERS.remove(self)

        # Remove all pending timeouts
        io_loop = tornado.ioloop.IOLoop.instance()
        for timeout in self.timeouts:
            io_loop.remove_timeout(timeout)


def schedule_redis_message(io_loop, element, *args):
    handle = io_loop.add_timeout(datetime.timedelta(seconds=DELAY_SECONDS),
                                 element.on_redis_message, *args)
    element.timeouts.append(handle)


def redis_listener(io_loop, pubsub):
    for message in pubsub.listen():
        for element in LISTENERS:
            io_loop.add_callback(schedule_redis_message, io_loop, element, message)


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
