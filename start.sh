#!/bin/bash
echo "🚀 SERVER IS STARTING ON PORT: $PORT"
uvicorn main:app --host 0.0.0.0 --port $PORT