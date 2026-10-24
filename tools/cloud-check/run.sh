#!/usr/bin/env bash
# 클라우드 사전 검증: (1) Core 테스트 (2) Unity 스크립트 컴파일. PC 의 Unity 검증 전에 오류 대부분을 잡는다.
# 사용: bash tools/cloud-check/run.sh   (dotnet 이 없으면 apt 로 설치: apt-get install -y dotnet-sdk-8.0)
set -e
cd "$(dirname "$0")"
command -v dotnet >/dev/null || { apt-get install -y -qq dotnet-sdk-8.0; }
echo "== [1/2] Core 규칙 컴파일 + NUnit 테스트"
dotnet test core-tests.csproj 2>&1 | grep -E "error|Passed!|Failed" || true
echo "== [2/2] Unity 화면 스크립트 컴파일(UnityEngine 2021.3 참조)"
dotnet build unity-scripts.csproj --no-incremental 2>&1 | grep -E " error |Build succeeded|Error\(s\)" | sort -u
