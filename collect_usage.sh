#!/usr/bin/env bash
# Collect Claude Code usage from this machine plus any number of remote hosts, then report the
# combined total. Claude Code keeps transcripts per-machine with no central ledger, so this is
# the only way to get a figure that is not silently a lower bound.
#
#   ./collect_usage.sh                          # this machine only
#   ./collect_usage.sh cluster                 # this machine + a remote host
#   ./collect_usage.sh cluster other-box       # ...and more
#
# Remote hosts need nothing but python3: the script is piped over stdin and run with --raw, which
# applies no rates and reads no data files. Only token counts come back, never message content.
#
# Remote transcript roots are auto-discovered ($HOME/.claude/projects plus any
# */.claude/projects on scratch-style paths), since they are not always under $HOME.
set -euo pipefail
cd "$(dirname "$0")"
OUT=$(mktemp -d)
trap 'rm -rf "$OUT"' EXIT

echo "[local] $(hostname -s)"
python3 measure_usage.py --raw > "$OUT/local.json"

for host in "$@"; do
  echo "[remote] $host — discovering transcript roots"
  # shellcheck disable=SC2029
  # Scope every candidate to $USER. A wildcard here (/scratch/*/...) matches OTHER PEOPLE's
  # directories on a shared cluster -- group-readable ones will silently inflate your total with
  # a colleague's usage, which is both wrong and not yours to read.
  roots=$(ssh -o BatchMode=yes "$host" '
    for d in "$HOME"/.claude/projects /scratch/"$USER"/.claude/projects \
             /project/*/"$USER"/.claude/projects; do
      [ -d "$d" ] && printf "%s\n" "$d"
    done' 2>/dev/null || true)
  if [ -z "$roots" ]; then
    echo "         no transcript roots found (or SSH window lapsed) — skipping"
    continue
  fi
  args=""
  while read -r r; do
    [ -n "$r" ] && args="$args --root $r" && echo "         $r"
  done <<< "$roots"
  # shellcheck disable=SC2086
  ssh -o BatchMode=yes "$host" "python3 - --raw $args" < measure_usage.py > "$OUT/$host.json"
done

echo
python3 measure_usage.py --merge "$OUT"/*.json
