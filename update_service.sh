#!/bin/bash

files=("app.service" "stream.service" "display_stats.service")
target_dir="$HOME/.config/systemd/user"

for f in "${files[@]}"; do
  if ! cmp -s "$f" "$target_dir/$f"; then
    cp "$f" "$target_dir/"
    echo "Copied $f"
  else
    echo "No changes in $f, skipping."
  fi
done