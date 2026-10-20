#!/usr/bin/env bash
set -e
project_directory="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate iptvapp
cd -- "$project_directory"
export QT_QPA_PLATFORM=wayland
exec python -s "$project_directory/main.py" "$@"
