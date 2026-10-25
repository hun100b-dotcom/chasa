// unity-test.mjs — Unity 배치모드 테스트/빌드 실행기 + 결과 요약기
//
// 이 파일이 왜 존재하는가:
//   Unity는 창 없이도(batchmode) 테스트·빌드를 돌릴 수 있지만, 명령이 길고 로그가 방대하다.
//   이 스크립트가 (1) 명령을 정확히 조립하고 (2) 잠금/경로를 먼저 확인하고 (3) 결과 XML에서
//   "통과/실패 개수와 실패 이름"만 뽑아 보여준다 → 채팅에 로그 전체를 붙일 일이 없어진다.
//
// 사용법:
//   node tools/unity-test.mjs                  # EditMode 테스트
//   node tools/unity-test.mjs --build-webgl    # WebGL 빌드 (BuildScript.BuildWebGL)
//   node tools/unity-test.mjs --parse a.xml    # 이미 있는 NUnit 결과 XML만 요약
// 종료코드: 0 통과 / 2 테스트 실패 / 1 그 외 오류
import { existsSync, readFileSync, mkdirSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { join } from 'node:path';

const ROOT = process.cwd();
const PROJECT = join(ROOT, 'unity');
const argv = process.argv.slice(2);

// NUnit 결과 XML에서 총계와 실패 케이스를 뽑는다 (정규식 파싱: 외부 라이브러리 없이 동작하게)
function summarize(xmlPath) {
  const xml = readFileSync(xmlPath, 'utf8');
  const run = xml.match(/<test-run\b[^>]*>/)?.[0] ?? '';
  const attr = (n) => run.match(new RegExp(`\\b${n}="([^"]*)"`))?.[1] ?? '?';
  console.log(`테스트 총 ${attr('total')} / 통과 ${attr('passed')} / 실패 ${attr('failed')} / 건너뜀 ${attr('skipped')} (소요 ${attr('duration')}초)`);
  const failed = [...xml.matchAll(/<test-case\b[^>]*result="Failed"[^>]*>[\s\S]*?<\/test-case>/g)];
  for (const m of failed) {
    const name = m[0].match(/\bfullname="([^"]*)"/)?.[1] ?? '(이름 불명)';
    const msg = (m[0].match(/<message>\s*(?:<!\[CDATA\[)?([\s\S]*?)(?:\]\]>)?\s*<\/message>/)?.[1] ?? '').trim().split('\n')[0];
    console.log(` ✗ ${name}\n     ${msg}`);
  }
  return Number(attr('failed')) > 0 ? 2 : 0;
}

const pi = argv.indexOf('--parse');
if (pi >= 0) process.exit(summarize(argv[pi + 1]));

// 에디터 경로: 환경변수 → ProjectVersion.txt 의 버전으로 기본 설치 위치 추정
const ver = readFileSync(join(PROJECT, 'ProjectSettings/ProjectVersion.txt'), 'utf8').match(/m_EditorVersion:\s*(\S+)/)[1];
const home = process.env.USERPROFILE || process.env.HOME || '';
const candidates = [
  process.env.UNITY_EDITOR_PATH,
  join(home, 'Unity/Editor', ver, 'Editor/Unity.exe'),
  `C:/Program Files/Unity/Hub/Editor/${ver}/Editor/Unity.exe`,
].filter(Boolean);
const unity = candidates.find(existsSync);
if (!unity) { console.error(`Unity ${ver} 를 못 찾음. 후보:\n` + candidates.join('\n')); process.exit(1); }

// 이미 다른 Unity가 이 프로젝트를 열고 있으면 실패하므로 먼저 막는다
if (existsSync(join(PROJECT, 'Temp/UnityLockfile'))) {
  console.error('unity/Temp/UnityLockfile 존재 — 다른 Unity가 열려 있을 수 있음. 끝난 뒤 다시 실행하세요.');
  process.exit(1);
}

mkdirSync(join(ROOT, 'unity/Logs'), { recursive: true });
const log = join(ROOT, 'unity/Logs/batch.log');
const xmlOut = join(ROOT, 'unity/Logs/editmode-results.xml');
const build = argv.includes('--build-webgl');
// 주의: -runTests 에는 -quit 를 붙이지 않는다(테스트 종료 전에 꺼질 수 있음)
const args = build
  ? ['-batchmode', '-nographics', '-quit', '-projectPath', PROJECT, '-executeMethod', 'BuildScript.BuildWebGL', '-logFile', log]
  : ['-batchmode', '-nographics', '-projectPath', PROJECT, '-runTests', '-testPlatform', 'EditMode', '-testResults', xmlOut, '-logFile', log];

console.log(`실행: ${unity}\n모드: ${build ? 'WebGL 빌드' : 'EditMode 테스트'}`);
const r = spawnSync(unity, args, { stdio: 'inherit' });

// 컴파일 에러 줄만 뽑아 보여준다 (로그 전체를 출력하지 않기 위해)
if (existsSync(log)) {
  const errs = readFileSync(log, 'utf8').split(/\r?\n/).filter((l) => /error CS\d+|Exception:/.test(l)).slice(0, 15);
  if (errs.length) console.log('--- 에러 줄 ---\n' + errs.join('\n'));
}
if (!build && existsSync(xmlOut)) process.exit(summarize(xmlOut) || (r.status ? 1 : 0));
process.exit(r.status === 0 ? 0 : 1);
