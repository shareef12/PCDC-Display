# Flag submission visualization

## Setup

    # Start redis
    docker pull redis
    ./redis.sh

    # Install python dependencies
    pip3 install tornado redis

    # Run the displayservice
    ./displayservice.py

    # Browse to localhost:8888
