// ip-scan.mjs — IP 금지어 검사기
//
// 이 파일이 왜 존재하는가:
//   AI 생성 프롬프트·게임 내 텍스트에 금지된 작품명/캐릭터명이 섞이면 "의도적 모방의 증거"가 된다.
//   사람 눈으로는 수백 개 문서에서 놓치므로, 기계가 먼저 걸러낸다.
//
// 사용법:
//   node tools/ip-scan.mjs                 # 기본 대상(게임에 들어가는/생성에 쓰이는 폴더) 검사
//   node tools/ip-scan.mjs docs/narrative  # 지정 경로만 검사 (파일 또는 폴더 여러 개 가능)
//   종료코드: 0 = 적중 없음, 1 = 적중 있음
//
// 예외: 한 줄에 `ip-scan:allow` 를 적으면 그 줄은 건너뛴다(금지 목록을 설명하는 문서 등).
//   IP-SAFETY·CLAUDE.md·에이전트/스킬/하네스 문서는 금지어를 "설명"하므로 기본 제외한다.
import { readdirSync, readFileSync, statSync, existsSync } from 'node:fs';
import { join, relative, extname, sep } from 'node:path';

// 금지어 목록 (docs/IP-SAFETY.md 와 같은 내용을 기계가 읽는 형태로 옮긴 것)
const BANNED = [
  // 《신과함께》 관련
  '신과함께', '강림', '해원맥', '덕춘', 'Along with the Gods',
  // 멸귀수도전 / 도깨비의 세계 관련
  '멸귀수도전', '도깨비의 세계',
  // 디아블로 고유명칭 (영감으로 언급하는 내부 문서는 대상에서 빠지지만, 프롬프트·게임 텍스트에는 금지)
  '디아블로', 'Diablo',
  // 슈퍼캣 도트 에셋
  '슈퍼캣', 'Supercat',
  // 기획 IP 전수 점검(planning/audit/ip_scan.py) 중 어디서든 고치는 낱말과 작품명. 기만·제압처럼 짧은 낱말은 오탐이 많아 뺐다(도술 이름 칸은 별도 확인)
  '김자홍', '진기한', '묘롱', '신식 개방', '낙화의 전장', '만귀비경', '승천탑', '프로젝트 OQ',
  '블리자드', 'Blizzard', '트리스트럼', 'Tristram', '호라드림', 'Horadric', '네팔렘', 'Nephalem', '릴리트', 'Lilith',
  '이나리우스', 'Inarius', '메피스토', 'Mephisto', '정복자 보드', 'Paragon', '케지스탄', 'Kehjistan', '세계석', 'Worldstone',
  '바람의나라', '로스트아크', 'Lost Ark', '아크라시아', '자그레우스', 'Zagreus', '패스 오브 엑자일', 'Path of Exile', 'PoE2',
  '레이크라스트', 'Wraeclast', '마비노기', 'Mabinogi', '밀레시안', '티르 코네일', '던바튼', '문게이트',
  '리니지', '귀멸의 칼날', '스마일게이트', 'Supergiant', 'Grinding Gear',
];

const ROOT = process.cwd();
// 인자가 없을 때 검사할 곳: 생성 프롬프트·게임 텍스트·데이터·유니티 에셋
const DEFAULT_TARGETS = ['assets', 'data', 'unity/Assets', 'docs/art', 'docs/narrative', 'planning'];
// 금지어를 "설명하기 위해" 적는 파일 — 기본 제외
const EXCLUDE = [
  'docs/IP-SAFETY.md', 'CLAUDE.md', 'docs/harness', '.claude', 'tools/ip-scan.mjs',
  'node_modules', '.git', 'Library', 'Temp', 'Build', 'Logs',
].map((p) => p.split('/').join(sep));
const TEXT_EXT = new Set(['.md', '.txt', '.json', '.cs', '.js', '.mjs', '.ts', '.html', '.css', '.svg', '.yaml', '.yml', '.csv']);

function isExcluded(rel) {
  return EXCLUDE.some((e) => rel === e || rel.startsWith(e + sep) || rel.split(sep).includes(e));
}

// 폴더를 재귀로 돌며 텍스트 파일 경로를 모은다 (바이너리·대용량 제외)
function* walk(p) {
  const rel = relative(ROOT, p);
  if (rel && isExcluded(rel)) return;
  const st = statSync(p);
  if (st.isDirectory()) {
    for (const name of readdirSync(p)) yield* walk(join(p, name));
  } else if (TEXT_EXT.has(extname(p).toLowerCase()) && st.size < 2_000_000) {
    yield p;
  }
}

const args = process.argv.slice(2);
const targets = (args.length ? args : DEFAULT_TARGETS).map((t) => join(ROOT, t)).filter(existsSync);

let hits = 0;
let files = 0;
for (const t of targets) {
  for (const f of walk(t)) {
    files++;
    const lines = readFileSync(f, 'utf8').split(/\r?\n/);
    lines.forEach((line, i) => {
      if (line.includes('ip-scan:allow')) return;
      const lower = line.toLowerCase();
      for (const w of BANNED) {
        if (lower.includes(w.toLowerCase())) {
          hits++;
          console.log(`${relative(ROOT, f)}:${i + 1}  [${w}]  ${line.trim().slice(0, 100)}`);
        }
      }
    });
  }
}
console.log(`\n검사 파일 ${files}개, 적중 ${hits}건 → ${hits ? '수정 필요' : '통과'}`);
process.exit(hits ? 1 : 0);
