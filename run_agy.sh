#!/bin/bash
# usage: run_agy.sh <model> <taskfile> <logfile> [timeout]
export HTTPS_PROXY=http://127.0.0.1:7890 HTTP_PROXY=http://127.0.0.1:7890
cd /workspace/anime-harbor-scene
/mnt/bot/box/.gemini/bin/agy --model "$1" --effort xhigh --dangerously-skip-permissions --print-timeout "${4:-120m}" --print "$(cat $2)" > "$3" 2>&1
echo "EXIT $?" >> "$3"
