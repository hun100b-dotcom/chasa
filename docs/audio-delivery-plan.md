# 소리 내려받기·압축 계획 (웹·폰) — 기획·사운드 → 코드팀 (2026-10-25 밤)

숫자는 [audio-budget.md](audio-budget.md)에 있다. `tools/audio_budget.py`가 재서 만든다. 막별 묶음표는 `data/audio_packs.json`이다.
이 문서는 **코드팀이 할 일**만 적는다. 사운드는 코드 파일을 고치지 않는다.

## 지금 문제 셋
1. **모든 소리가 `Resources/` 안에 있다.** Unity 웹판은 Resources 안의 것을 첫 데이터 파일에 전부 넣는다. 그래서 1막만 하는 사람도 8막 소리까지 처음에 다 받는다.
2. **압축 품질이 100%다.** 모든 오디오 `.meta`가 `compressionFormat: 1 (Vorbis)`, `quality: 1`이다. 이대로 구우면 효과음 약 40MB, 음악 약 119MB가 된다.
3. **불러오기 방식이 전부 DecompressOnLoad다(`loadType: 0`).** 웹은 이 방식이면 소리를 풀어서(48kHz, 4바이트) 메모리에 든다. 2분짜리 스테레오 곡 하나가 약 46MB다. 또 Unity 문서에 따르면 iOS가 무음 모드일 때 DecompressOnLoad 소리는 안 들릴 수 있다. CompressedInMemory는 괜찮다([Unity 6 Web 오디오](https://docs.unity3d.com/6/Documentation/Manual/webgl-audio.html)).

## 1) 가져오기 설정 바꾸기 (가장 싸고 효과 큼)
`data/audio_packs.json`의 `kind_of`가 소리마다 다섯 종류 중 하나를 정해 둔다. 종류별 설정은 `import`에 있다.

| 종류 | 무엇 | 불러오기 | 표본율 | 목표 크기(웹 AAC / 폰 Vorbis) |
|---|---|---|---|---|
| sfx_short | 타격·UI처럼 짧고 높은 소리 | DecompressOnLoad (지연 없이 바로) | 44100 | 64kbps / 품질 0.4 |
| sfx_lowband | 11kHz 위가 거의 없는 짧은 소리 | DecompressOnLoad | **22050** | 48kbps / 0.3 |
| amb_loop | 반복 환경음 | **CompressedInMemory** | **22050** | 48kbps / 0.3 |
| long_oneshot | 8초 넘는 한 번 소리 | **CompressedInMemory** | 44100 | 56kbps / 0.3 |
| bgm | 음악 | **CompressedInMemory** + Load In Background | 44100 | 80kbps / 0.3 |

- Unity 웹은 품질 슬라이더를 AAC로 바꿔 굽는다. 슬라이더 값이 몇 kbps가 되는지는 Unity 안에서만 알 수 있다. 처음 한 번 빌드한 뒤 Editor.log 빌드 보고서의 오디오 크기를 보고, 위 표의 합계에 맞을 때까지 슬라이더를 조정해 주세요. 대략 0.3~0.5가 될 것으로 봅니다.
- 이 설정을 `.meta` 342개에 손으로 넣지 말고, 에디터 스크립트(AssetPostprocessor 의 OnPreprocessAudio)가 `data/audio_packs.json`의 `kind_of`를 읽어 정하게 하면 새 소리도 저절로 맞는다.
- `normalize: 1`은 Force To Mono를 켰을 때만 작동하므로 지금은 영향이 없다. 우리 파일은 크기를 이미 맞춰 두었으니 끄는 쪽이 안전하다.
- 11kHz 위를 잘라도 되는 것은 측정으로 골랐다(11kHz 위 에너지가 전체보다 40dB 넘게 작은 것). 웹은 브라우저가 어차피 48kHz로 풀기 때문에 메모리는 줄지 않고 **내려받기만** 준다.

## 2) 막별로 나눠 받기
- **묶음:** core(공통) · act1 · act2 · act3 · s2 · act6 · act7 · act8. 목록은 `data/audio_packs.json`의 `packs`에 있다.
  - core에는 UI·발소리·전투·처결·날씨가 들어 있다. 어느 막이든 쓰는 것들이다.
  - 컷신 소리는 대본에서 처음 쓰이는 막에 넣었다.
  - 보스 소리는 보스 번호로 막을 정했다.
- **제안 방식:** 추가 패키지가 필요 없는 AssetBundle을 쓴다.
  - 오디오를 `Resources/` 밖, 예를 들어 `Assets/AudioPacks/<묶음>/`로 옮긴다.
  - 묶음마다 AssetBundle 이름을 `audio_<묶음>`으로 붙여 StreamingAssets에 굽는다.
  - 웹에서는 `UnityWebRequestAssetBundle.GetAssetBundle(url, hash)`로 받는다. 브라우저 캐시에 남는다(`webGLDataCaching: 1`은 이미 켜져 있음).
  - Addressables도 되지만 패키지와 설정이 늘어난다.
- **받는 순서:**
  1. 시작할 때 `core` + `act1`을 받는다.
  2. 1막을 하는 동안 뒤에서 `act2`를 미리 받는다.
  3. N막에 들어서면 N+1막 묶음을 받는다.
  4. 시즌3부터 시작하는 사람(C-21S)은 `act6`을 먼저 받는다.
- **받는 중에 소리를 부르면:** 지금 `Sfx.cs`는 파일이 없을 때 코드 합성(SfxSynth)으로 대신한다. 묶음이 아직 안 왔을 때도 이 길을 그대로 쓰면 된다. 음악은 지금처럼 `Load(id) ?? Temp`를 쓰고, 둘 다 없으면 무음으로 둔다.
- **다 쓴 묶음:** 폰 메모리를 생각하면 두 막 전 묶음은 `Unload(false)`로 내려도 된다. 다시 필요하면 캐시에서 금방 온다.

## 3) 그 밖에
- `ProjectSettings` 의 `webGLCompressionFormat: 2`(압축 안 함)는 코드·그림까지 압축 없이 보낸다. 소리는 이미 압축돼 있어 영향이 작지만, 전체 크기를 생각하면 Brotli(0)나 Gzip(1)을 켜 주세요. 그러려면 Vercel이 `Content-Encoding` 머리말을 붙여 주는지 확인해야 한다. 안 되면 `webGLDecompressionFallback: 1`을 켠다.
- 처음 소리는 사람이 화면을 한 번 눌러야 난다(브라우저 자동재생 막기). 시작 화면의 "누르면 시작"에서 오디오를 깨우면 된다.

## 사운드 쪽에서 이미 한 것
- 클리핑과 음량을 한꺼번에 검사했다.
  - 샘플 최고점이 0dB에 닿은 파일은 없다.
  - 트루 피크가 −1dB를 넘은 것은 `bgm_solgogae_finish`(진짜 곡, −0.8dB) 하나다. AAC로 구우면 넘칠 수 있으니 가져오기에서 소리를 키우지 말 것. 다음에 그 곡을 다시 내보낼 때 −1dB로 맞추겠습니다.
- 요령방울 타격(`sfx.hit.bell`, `.heavy`)이 다른 무기 타격보다 약 8dB 크게 들려서 4dB 내렸다.
- 그 밖에 튀는 것은 일부러 그렇게 만든 것이다. 처결 대기 틱은 작게, 품계 오름은 크게 했다.
