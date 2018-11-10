#!/usr/bin/env python3

"""
Live attack-defend CTF visualization.

This script implements a web server that allows for live viewing of an ongoing
attack-defend CTF competition. Users can browse to the server's address for
a visualization of events occurring on the CTF network. Events may include
items such as network traffic on certain services or flag submission.

Events are published to a Redis pubsub queue, and consumed by this server.
After a configurable delay, they are then published to connected clients for
display. It is up to the integrator to determine which events are published and
when, along with how teams and events are displayed.
"""

import argparse
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
REDIS_PUBSUB_NAME = "ctfview"

TEAMS = [
    {"name": "army",     "display_name": "Army",      "location": "left",   "color": "Olive"},
    {"name": "airforce", "display_name": "Air Force", "location": "right",  "color": "Blue"},
    {"name": "observer", "display_name": "Observer",  "location": "top",    "color": "Red"},
    {"name": "zombie",   "display_name": "Zombie",    "location": "bottom", "color": "DimGray"},
]

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
    """Tornado handler for basic requests."""

    def get(self):
        self.render("index.html")


class WebSocketChatHandler(tornado.websocket.WebSocketHandler):
    """Tornado handler for incoming websocket connections.

    A new WebSocketChatHandler object will be instantiated for each connected
    client. Incomining redis messages will passed to all connected websocket
    handlers via the on_redis_message callback after a specified delay.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, *kwargs)
        self.timeouts = []

    def open(self):
        """Initialize the client by sending the legend and team locations."""
        logger.info("Websocket opened")
        LISTENERS.append(self)

        logger.info("Initializing legend")
        msg = {"type": "legend", "services": SERVICES}
        self.write_message(json.dumps(msg))

        logger.info("Initializing teams")
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

        msg = {
            "type": "traffic",
            "from": from_team,
            "to": to_team,
            "size": size,
            "color": color}
        self.write_message(json.dumps(msg))

    def on_close(self):
        """Clean up - cancel any pending events scheduled for this client."""
        print("[*] Closing connection.")
        LISTENERS.remove(self)

        # Remove all pending timeouts
        io_loop = tornado.ioloop.IOLoop.instance()
        for timeout in self.timeouts:
            io_loop.remove_timeout(timeout)


def schedule_redis_message(io_loop, handler, *args):
    """Callback to schedule a callback after a specified delay."""
    handle = io_loop.add_timeout(datetime.timedelta(seconds=DELAY_SECONDS),
                                 handler.on_redis_message, *args)
    handler.timeouts.append(handle)


def redis_listener(io_loop, pubsub):
    """Thread callback to handle received redis messages.

    Publish each message to every connected websocket client after a specified
    delay. Since tornado's IOLoop.add_timeout() must be called from the event
    loop thread, schedule a callback to do this on the correct thread.
    """
    for message in pubsub.listen():
        for handler in LISTENERS:
            io_loop.add_callback(schedule_redis_message, io_loop, handler, message)


def serve_forever(port, redis_server):
    """Start a thread to listen for redis messages and start the app."""
    # Subscribe to the redis pubsub queue and start a thread to dispatch messages
    ps = redis_server.pubsub()
    ps.subscribe(REDIS_PUBSUB_NAME)

    io_loop = tornado.ioloop.IOLoop.instance()
    t = threading.Thread(target=redis_listener, args=(io_loop, ps))
    t.setDaemon(True)
    t.start()

    # Start the app on the specified port
    handlers = [
        ("/", IndexHandler),
        ("/websocket", WebSocketChatHandler),
    ]
    settings = {
        "static_path": os.path.join(os.path.dirname(__file__), "static")
    }

    app = tornado.web.Application(handlers, **settings)
    app.listen(port)
    print("[*] Waiting on browser connections...")
    io_loop.start()


def main():
    parser = argparse.ArgumentParser(description="Run an attack-defend CTF visualization",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-p", "--port", type=int, default=8888,
                        help="Port to listen on.")
    parser.add_argument("-r", "--redis-host", default="localhost",
                        help="Hostname of redis server to connect to.")
    parser.add_argument("--redis-port", type=int, default=6379,
                        help="Port of redis server to connect to.")

    args = parser.parse_args()

    try:
        redis_server = redis.StrictRedis(host=args.redis_host, port=args.redis_port)
    except redis.ConnectionError:
        logger.exception("Unable to connect to Redis!")
        return

    serve_forever(args.port, redis_server)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[*] Server is quitting...")
        sys.exit(0)
