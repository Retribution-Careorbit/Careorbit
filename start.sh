#!/bin/bash
pkill -f "python main.py" 2>/dev/null
pkill -f "uvicorn" 2>/dev/null
sleep 1

python main.py &
FASTAPI_PID=$!

sleep 2

npm run dev &
NPM_PID=$!

cleanup() {
  kill $FASTAPI_PID $NPM_PID 2>/dev/null
  wait $FASTAPI_PID $NPM_PID 2>/dev/null
}

trap cleanup EXIT SIGTERM SIGINT
wait
