#!/bin/bash

if [[ "$1" == "--kill" ]]; then
    # Find the process ID of 'python3 bot.py' and kill it
    PID=$(ps -aux | grep '[p]ython3 bot.py' | awk '{print $2}')
    if [ -z "$PID" ]; then
        echo "No 'python3 bot.py' process found."
    else
        kill $PID
        echo "'python3 bot.py' process killed."
    fi
elif [[ "$1" == "--start" ]]; then
    # Start 'python3 bot.py' in the background
    nohup python3 bot.py &
    echo "'python3 bot.py' started in the background."
else
    echo "Invalid option. Use --kill to kill the process or --start to start it."
fi