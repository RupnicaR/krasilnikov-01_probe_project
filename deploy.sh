#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

VERSION=${1:?usage: bash deploy.sh 5.0}
PREFIX=krasilnikov-01
PORT=8003
REGISTRY=localhost:6001
IMAGE=$REGISTRY/$PREFIX/probe:$VERSION

if [ "$(docker info --format '{{.Swarm.LocalNodeState}}')" != active ]; then
  docker swarm init --advertise-addr 127.0.0.1
fi

if ! docker ps -a --format '{{.Names}}' | grep -qx "$PREFIX-registry"; then
  docker volume create "$PREFIX-registry" >/dev/null
  docker run -d --restart unless-stopped --name "$PREFIX-registry" \
    -p 6001:5000 -v "$PREFIX-registry:/var/lib/registry" registry:2
fi
if [ "$(docker inspect -f '{{.State.Running}}' "$PREFIX-registry")" != true ]; then
  docker start "$PREFIX-registry" >/dev/null
fi
until curl -sf "$REGISTRY/v2/" >/dev/null; do sleep 1; done

docker build --build-arg VERSION="$VERSION" -t "$IMAGE" .
docker push "$IMAGE"
VERSION="$VERSION" docker stack deploy --detach=false -c stack.yaml "$PREFIX"

SECONDS=0
until curl -sf -m 2 "http://127.0.0.1:$PORT/notes" >/dev/null; do
  if [ "$SECONDS" -ge 90 ]; then
    echo "application did not answer in 90 seconds" >&2
    exit 1
  fi
  sleep 2
done
curl -s "http://127.0.0.1:$PORT/notes"; echo
