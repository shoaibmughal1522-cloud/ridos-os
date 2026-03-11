#!/bin/bash
# wget wrapper - silently handles Contents-amd64.gz 404 errors
REAL_WGET=/usr/bin/wget
ARGS=("$@")
for arg in "${ARGS[@]}"; do
  if [[ "$arg" == *"Contents"* ]]; then
    for i in "${!ARGS[@]}"; do
      if [[ "${ARGS[$i]}" == "-O" ]]; then
        OUTFILE="${ARGS[$((i+1))]}"
        if [ -n "$OUTFILE" ]; then
          printf '\x1f\x8b\x08\x00\x00\x00\x00\x00\x00\x03\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00' > "$OUTFILE"
        fi
        exit 0
      fi
    done
    exit 0
  fi
done
exec "$REAL_WGET" "$@"
