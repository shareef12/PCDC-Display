#!/bin/bash

docker pull redis
docker run --name redis --rm -d -p 6379:6379 redis
