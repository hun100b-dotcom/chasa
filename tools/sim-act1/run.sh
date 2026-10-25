#!/usr/bin/env bash
# 1막 천도만 / 파혼만 / 섞기 자동 시뮬 → 수치표. 사용: bash tools/sim-act1/run.sh [판 수, 기본 4000]
cd "$(dirname "$0")"
command -v dotnet >/dev/null || apt-get install -y -qq dotnet-sdk-8.0
dotnet run -c Release --project sim-act1.csproj -- "${1:-4000}"
