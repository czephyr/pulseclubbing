#!/bin/bash

# Load environment variables from .env file in the current directory
if [ -f .env ]; then
    export $(cat .env | xargs)
else
    echo ".env file not found"
    exit 1
fi

# Function to display help
show_help() {
    echo "Usage: $0 [OPTION]"
    echo "Options:"
    echo "  --copy-db-locally  Copy the database file from a remote server to the local machine."
    echo "  -h, --help         Display this help and exit."
}

# Check the arguments
if [ "$1" = "--copy-db-locally" ]; then
    # Copy the database file using scp
    scp ${PIZERO_USERNAME}@${PIZERO_IP}:${PIZERO_DATABASE_PATH} .
elif [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    # Show help
    show_help
else
    echo "Invalid option. Use --help for more information."
    exit 2
fi
