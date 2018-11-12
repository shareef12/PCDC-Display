# ctfview

`ctfview` provides a configurable real-time visualization for attack-defend CTF
competitions. This display can be used to visualize network traffic, flag
submission, or other activities occurring between teams.

<img src="https://media.giphy.com/media/toAg1GIddD0Ffz9enq/giphy.gif" width="500">


## Running ctfview

The `ctfview` web server receives events to display from a Redis
publisher/subscriber queue. It is up to the CTF integrator to determine how and
when events are published to this queue. A test script is provided to publish
sample data.

### Installation

To install ctfview, you must first install Redis and python dependencies. Redis
can be installed using your distribution package manager. Alternatively, you
can use the latest Redis docker image.

    # Start redis
    docker pull redis
    docker run --name redis --rm -d -p 6379:6379 redis

    # Install python dependencies
    pip3 install -r requirements.txt

Ensure redis is listening and can be reached from the server that will run
`ctfview`.

### Running

To run the `ctfview` web server, execute `ctfview.py` on the command line. It
will begin listening on a default port of 8888.

    # Run the web server
    ./ctfview/ctfview.py

Browse to `localhost:8888` to view the visualization. The provided `test.py`
script can be used to publish test data to the redis queue.


## Integrating ctfview into a CTF

### Adding teams

To add teams, modify the global `TEAMS` array in `ctfview/ctfview.py`. For each
team, the following fields must be defined:

* `name` - Unique identifier for the team.
* `display_name` - Team name that will be displayed in the visualization.
* `location` - Relative team location. One of:
  * `top-left`
  * `left`
  * `bottom-left`
  * `top`
  * `center`
  * `bottom`
  * `top-right`
  * `right`
  * `bottom-right`
* `color` - Team color. Valid options are HTML color names, hex color codes, or
            RGB values.

### Adding services

To add services, modify the global `SERVICES` array in `ctfview/ctfview.py`.
For each service, the following fields must be defined:

* `name` - Unique identifier for the service.
* `color` - Service color. Valid options are HTML color names, hex color codes,
            or RGB values.

### Publishing events

All events should be published to Redis "ctfview" pubsub queue. Events received
from the queue will not be displayed until a configurable delay has passed. To
set the delay, modify the `DELAY_SECONDS` variable in `ctfview/ctfview.py`. The
delay will default to one second. Events consist of a JSON blob with the
following fields:

* `service` - The service name corresponding to this event.
* `from` - The originating team name.
* `to` - The destination team name.
* `size` - Size of the event. This field is useful for depicting network
           traffic where each event is a packet.

It is up to the integrator to determine how to publish events to the Redis
queue. In python, it is straightforward to use the redis library to do this.

    redis_server = redis.StrictRedis(host=args.redis_host, port=args.redis_port, db=0)
    data = {
        "service": "shipyard",
        "from": "army",
        "to": "airforce",
        "size": 5,
    }
    data = json.dumps(data)
    redis_server.publish("ctfview", data)

By default, `ctfview` will use the missiles animation. To use the circles
animation instead, set `ANIMATION_TYPE` to `circle` in `ctfview/index.html`.


## Copyright

Copyright for portions of the project are held by github user sjcappella, 2015
as part of project PCDC-Display. All other copyright are held by Christian
Sharpsten, 2018.
