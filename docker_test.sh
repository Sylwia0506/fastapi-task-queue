#!/bin/bash

echo "Building and starting containers..."
docker-compose up -d --build

echo "Waiting for services to be ready..."
sleep 10

echo "Running test client..."
docker-compose run --rm web python test_client.py

echo -e "\nContainer logs:"
docker-compose logs

echo -e "\nStopping containers..."
docker-compose down 