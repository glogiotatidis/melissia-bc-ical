#!/usr/bin/env bash
# Script to build and run the calendar generator

set -e

echo "Building container image..."
if command -v podman &> /dev/null; then
    echo "Using podman..."
    podman build -t melissia-bc-calendar .
    echo "Running calendar generator..."
    podman run --rm -v ./output:/app/output melissia-bc-calendar
elif command -v docker &> /dev/null; then
    echo "Using docker..."
    docker build -t melissia-bc-calendar .
    echo "Running calendar generator..."
    docker run --rm -v ./output:/app/output melissia-bc-calendar
else
    echo "Error: Neither docker nor podman found. Please install one of them."
    exit 1
fi

echo "Done! Check the output/ directory for generated files."
