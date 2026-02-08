#!/bin/bash

# Kill existing Metro
PORT=8081
PID=$(lsof -t -i:$PORT 2>/dev/null)
if [ -n "$PID" ]; then
  echo "Killing Metro Bundler (PID: $PID)"
  kill -9 $PID
  sleep 2
fi

# Start Metro from mobile directory
cd "$(dirname "$0")"
echo "Starting Metro from: $(pwd)"
npx expo start
