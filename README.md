# Docker DevOps Homework 2

Variant 01 project for a Docker Swarm stack with two web replicas, PostgreSQL,
a private registry, a multi-stage image build, and a repeatable deployment script.

Run `bash deploy.sh 5.0` to deploy the first version, then `bash deploy.sh 5.1`
to perform a rolling update. The service is available on `http://127.0.0.1:8003`.
