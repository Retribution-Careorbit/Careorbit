#!/bin/bash
python main.py &
FASTAPI_PID=$!
sleep 1
npm run dev &
NPM_PID=$!
trap "kill $FASTAPI_PID $NPM_PID 2>/dev/null" EXIT
wait
