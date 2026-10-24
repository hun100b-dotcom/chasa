"""Higgsfield 프롬프트 팩 생성기: assets/sprites/manifest.json 의 파일마다 프롬프트를 1:1로 만든다.
규칙(art-prompt-gate): 작품명·작가명 0개, 팔레트는 HEX 직접 명시, 주인공 고정 5요소, 네거티브에 일본 사신 도상, 변수 1개씩.
결과 파일: assets/prompts/higgsfield/PROMPT-PACK.json — 파일 하나 = 프롬프트 하나(생성 결과는 같은 이름으로 assets/final/ 에 둔다)."""
import json, os
ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
man = json.load(open(os.path.join(ROOT, "assets", "sprites", "manifest.json")))["sprites"]

STYLE = ("Korean folk dark-fantasy game art, painterly gothic with traditional dancheong accent colors, quarter-view 45 degree 2:1 isometric camera, "
         "low-key lighting, desaturated navy ambient light #16213E, deep shadow #0F1729, teal rim light #4FA8A0, warm hanji paper texture #F3E7D3, "
         "soft contact shadow, clean readable silhouette that still reads when filled solid black")
BG = "isolated on a flat solid #00FF00 chroma-key background, no ground, no text"
NEG = ("scythe, skull face, kimono, hooded robe, pixel art, photorealistic, text, watermark, logo, extra limbs, "
       "cropped, busy background, anime style")
CHASA = ("a Korean afterlife escort in a tall black horsehair hat (heukrip) with a wide flat brim, long black overcoat (dopo) with wide sleeves, "
         "a red sash #E85C41 at the waist, a chain (cheolsak) in pale blue #BFE8FF, and a small floating teal soul-flame #5FE3C0 near the shoulder")

S = {}   # 파일 경로(확장자 없음) → (주제 문장, 레퍼런스, 변수)
def add(k, subj, ref="", var=""): S[k] = (subj, ref, var)

# 주인공 — 첫 승인 이미지를 레퍼런스 시트로 고정(chasa_idle)
add("characters/chasa_idle", f"front view of {CHASA}, standing relaxed, chain hanging from the right hand", "", "기준 포즈")
for k, v in {"walk_a": "mid-stride, body leaning slightly left", "walk_b": "mid-stride, body leaning slightly right",
             "swing": "right arm extended sideways whipping the chain in a wide arc, glowing tip", "cast": "both hands held together in front of the chest, a bright teal soul orb between the palms, calm focused stance",
             "hit": "flinching backward, body tinted with a red flash", "bang1": "raising a six-sided wooden club (yukmo-bangmangi) above the shoulder, winding up",
             "bang2": "swinging the six-sided wooden club diagonally downward, mid-swing", "bang3": "club slammed on the ground with a red shock ring spreading around the feet"}.items():
    add(f"characters/chasa_{k}", f"{CHASA}, {v}", "characters/chasa_idle", "포즈만 변경")
# 혼 4종
add("enemies/soul_fresh", "a freshly dead soul, almost a living person, clear outline and readable sad face, pale-blue hanbok-like clothes #BFE8FF, translucent glow", "", "기준: 갓 죽은 혼 10초")
add("enemies/soul_fresh_kneel", "the same freshly dead soul kneeling with head bowed, waiting", "enemies/soul_fresh", "포즈만 변경")
add("enemies/soul_day", "a soul that wandered past a day, outline blurring, lower body dissolving like ink in water, amber glow #FFCC55, faint face", "", "기준: 해 넘긴 혼 7초")
add("enemies/soul_day_kneel", "the same blurred amber soul kneeling", "enemies/soul_day", "포즈만 변경")
add("enemies/soul_old", "an old wandering soul, proportions collapsed, long thin arms, no face, orange-red glow #FF6A3D, ragged lower edge", "", "기준: 오래된 혼 4초")
add("enemies/soul_old_kneel", "the same collapsed orange soul kneeling", "enemies/soul_old", "포즈만 변경")
add("enemies/soul_lump", "a mass of many tangled souls merged into one purple clump #9A5CFF, fragments of hands and faces poking out, a closed red dotted chain ring around its base", "", "기준: 덩어리(천도 불가)")
add("enemies/soul_fierce", "a fierce enraged soul, the old orange soul with a red flame aura #FF2A2A and small horn-like flames", "enemies/soul_old", "불길만 추가")
# 보스
add("boss/boss_naru_idle", "an old ferryman with a straw hat standing on a half-sunken wooden boat in misty river, pale-blue ghostly skin, five old coins on the deck, a pole planted in the water", "", "기준: 1호 보스")
add("boss/boss_naru_attack", "the same old ferryman pulling the pole far back to sweep, a red dotted warning arc in front", "boss/boss_naru_idle", "포즈만 변경")
# 타일
TILE = {"dirt_road": "packed brown earth path with small pebbles", "yard": "darker packed earth yard in front of a house", "grass": "dark green night grass with short blades",
        "paddy": "flooded barley paddy with water reflections between green rows", "stone_path": "flat grey stone slabs paving, shrine ground",
        "stepping_stones": "shallow stream with flat stepping stones"}
for t, d in TILE.items():
    for v in "ab":
        add(f"tiles/tile_{t}_{v}", f"a single seamless 128x64 isometric diamond ground tile: {d}, top-down lighting, no objects, edges tileable", "", f"변형 {v}")
# 소품
PR = {"choga": "a thatched-roof farmhouse (choga) with a wooden door and warm window", "giwa": "a tiled-roof house (giwa) with upswept eaves and wooden lattice doors",
      "stone_wall": "a low fieldstone wall segment", "jars": "three earthenware storage jars of different sizes (jangdok)", "well": "a stone village well with a wooden frame and bucket",
      "seonang_tree": "a huge old guardian tree with five-color cloth strips (blue, yellow, red, white, black) hanging from its branches", "cairn": "a small stacked-stone cairn",
      "jangseung": "a carved wooden village guardian post with a stern face (jangseung)", "sangyeo": "a funeral bier (sangyeo) with a gold-trimmed roof, white cloth and red band",
      "pyeongsang": "a low wooden platform bench (pyeongsang)", "jigae": "a wooden A-frame carrying rack (jigae)", "sotdae": "a tall wooden pole topped with a carved teal bird (sotdae)",
      "seonangdang": "a small roadside shrine house (seonangdang) with stone cairn and five-color cloths"}
for k, d in PR.items():
    add(f"props/prop_{k}", f"{d}, quarter-view isometric prop, footprint sits on the ground diamond", "", "소품 하나씩")
# 이펙트
add("fx/fx_call_0", "flat ground-aligned effect, a wide teal ring of soul-flames #5FE3C0 beginning to pull inward, 2:1 ellipse, transparent glow", "", "프레임 0/3")
add("fx/fx_call_1", "same effect, ring tighter, flames streaming toward the center", "fx/fx_call_0", "프레임 1/3")
add("fx/fx_call_2", "same effect, small bright ring, flames gathered", "fx/fx_call_0", "프레임 2/3")
add("fx/fx_bind_0", "flat ground-aligned effect, wide concentric dashed pale-blue chains #BFE8FF spiraling around a target, 2:1 ellipse", "", "프레임 0/3")
add("fx/fx_bind_1", "same effect, chains tightening", "fx/fx_bind_0", "프레임 1/3")
add("fx/fx_bind_2", "same effect, chains cinched small with a red core #E85C41", "fx/fx_bind_0", "프레임 2/3")
add("fx/fx_burst_0", "flat ground-aligned effect, a dark purple grudge-stain bulging with red cracks #E85C41, 2:1 ellipse", "", "프레임 0/3")
add("fx/fx_burst_1", "same effect, bursting outward in purple and red shards", "fx/fx_burst_0", "프레임 1/3")
add("fx/fx_burst_2", "same effect, large fading shock ring with scorch mark", "fx/fx_burst_0", "프레임 2/3")
for i in range(3):
    add(f"fx/stain_{i}", f"flat ground decal, dark purple grudge-stain #7B4FD6 with thin red cracks, overlap level {i+1} of 3, 2:1 ellipse", "", f"겹침 {i+1}")
for g, c in [("common", "#F3E7D3"), ("crafted", "#4FA8A0"), ("rare", "#D4A94E"), ("named", "#E85C41")]:
    add(f"fx/loot_{g}", f"a small dropped bundle on the ground with a vertical light pillar in {c}, grade {g}", "", "등급색만 변경")
# 아이콘
G = {"common": "plain", "crafted": "teal-accented, finely worked", "rare": "gold-trimmed with engraved pattern"}
for g, d in G.items():
    add(f"icons/icon_weapon_{g}", f"game item icon: a six-sided wooden club (yukmo-bangmangi), {d}, diagonal, centered", "", "등급만 변경")
    add(f"icons/icon_dopo_{g}", f"game item icon: a Korean overcoat (dopo) front view, {d}, centered", "", "등급만 변경")
    add(f"icons/icon_noriga_{g}", f"game item icon: a knotted ornamental charm with tassels (noriga), {d}, centered", "", "등급만 변경")
add("icons/icon_named_wolhwa_bell", "game item icon: a shaman's brass hand bell with a red tassel and red inscription, centered", "", "이름 있는 물건")
for g, c in [("common", "#F3E7D3"), ("crafted", "#4FA8A0"), ("rare", "#D4A94E"), ("named", "#E85C41")]:
    add(f"icons/frame_{g}", f"empty rounded-square item frame, border color {c}, dark navy interior #0F1729, thin inner line", "", "테두리 색만 변경")
# HUD
H = {"gauge_frame": "a slim pill-shaped gauge frame, gold #D4A94E border, empty dark navy inside", "gauge_fill": "a plain white pill bar to be tinted in engine",
     "timer_ring_bg": "a circular timer ring background, dark with thin gold double ring", "timer_ring_fill": "a plain thick white ring for radial fill",
     "btn_cheondo": "a round button icon: a teal soul-flame #5FE3C0 inside a dark circle with teal border", "btn_pahon": "a round button icon: a red crack symbol #E85C41 inside a dark circle with red border",
     "icon_neok": "a small teal soul-flame icon", "icon_memory": "a small torn hanji paper note icon with violet #C9B0FF edge", "icon_yeopjeon": "a small gold square-holed copper coin icon",
     "icon_karma": "a small dark knot icon with red thread #E85C41", "vision_vignette": "a full-screen dark navy ink-wash vignette, transparent center fading to opaque edges #0F1729",
     "memory_rim": "a thin soft white ring glow vignette, transparent center and edge", "night_bar": "a horizontal time bar from sunset orange through deep navy to pale dawn blue, gold border",
     "night_marker": "a small crescent moon marker with gold outline", "panel_hanji": "a dark navy UI panel with gold corner brackets, nine-slice friendly",
     "tilt_bar": "a thin horizontal slider track gradient from teal to red with a center tick", "tilt_marker": "a small hanji-colored diamond marker",
     "joystick_base": "a large translucent circular joystick base with dashed inner ring, gold outline", "joystick_knob": "a joystick knob, dark circle with teal border and glow",
     "btn_skill_call": "a round skill button icon: teal ring and inward soul-flames", "btn_skill_bind": "a round skill button icon: concentric dashed pale-blue chains with a red core",
     "btn_skill_burst": "a round skill button icon: a red and violet star-shaped burst", "btn_weapon_swap": "a round button icon: two opposing arrows, gold border", "btn_plus": "a round plus button, teal",
     "banner_result": "an ornamental horizontal banner frame with gold corner brackets, empty inside, nine-slice friendly"}
for k, d in H.items():
    add(f"hud/{k}", f"flat UI asset: {d}", "", "UI 하나씩")

# ② 검은여울 변형 — 기본 혼과 같은 그림에 석회색 반점(#C8C3A0)과 지워진 이름 먹줄만 추가(변수 1개)
for st, base, nm in [("fresh", "soul_fresh", "freshly dead"), ("day", "soul_day", "day-old"), ("old", "soul_old", "old")]:
    add(f"enemies/{base}_plague", f"the same {nm} soul with pale lime-white plague spots #C8C3A0 on the torso and two black ink strike-through lines across the chest, faint lime dust motes above the head", f"enemies/{base}", "역병 표식만 추가")
    add(f"enemies/{base}_kneel_plague", f"the same kneeling {nm} soul with pale lime-white plague spots #C8C3A0 and two black ink strike-through lines across the chest", f"enemies/{base}_kneel", "역병 표식만 추가")
for k, d in {"gauge_frame_r2": "a horizontal gauge frame with pale lime #C8C3A0 border and notched corners, empty inside, nine-slice friendly",
             "panel_hanji_r2": "a square UI panel with pale lime #C8C3A0 border, corner brackets, notch at top and bottom center, dark navy #16213E fill, nine-slice friendly",
             "timer_ring_bg_r2": "a circular timer ring background with thin pale lime #C8C3A0 outer line and a dotted inner ring on dark navy",
             "night_bar_r2": "a horizontal night-time progress bar gradient from overcast grey-blue #5A6B8C to deep navy #0F1729 to dawn blue #3A5A7C, pale lime frame"}.items():
    add(f"hud/{k}", f"flat UI asset: {d}", f"hud/{k[:-3]}", "지역 색만 변경")

# ③ 붉은재 / ④ 쇳골 변형 — 기본 혼 그림에 지역 표식만 추가
for st, base, nm in [("fresh", "soul_fresh", "freshly dead"), ("day", "soul_day", "day-old"), ("old", "soul_old", "old")]:
    for suf, kn in [("", ""), ("_kneel", "kneeling ")]:
        add(f"enemies/{base}{suf}_r3", f"the same {kn}{nm} soul wearing a small paper number tag on the chest and a rusty arrow stuck in the side, no flags, no national symbols", f"enemies/{base}{suf}", "번호 패·화살만 추가")
        add(f"enemies/{base}{suf}_r4", f"the same {kn}{nm} soul speckled with black coal dust and a small wooden miner number tag hanging at the chest", f"enemies/{base}{suf}", "석탄 가루·목패만 추가")
for r, col, nm in [(3, "#B0704F rust", "rusty red"), (4, "#B8A26A brass", "brass")]:
    for k, d in {"gauge_frame": f"a horizontal gauge frame with {nm} {col} border, empty inside, nine-slice friendly",
                 "panel_hanji": f"a square UI panel with {nm} {col} border and corner brackets, dark navy #16213E fill, nine-slice friendly",
                 "timer_ring_bg": f"a circular timer ring background with thin {nm} {col} outer line on dark navy"}.items():
        add(f"hud/{k}_r{r}", f"flat UI asset: {d}", f"hud/{k}", "지역 색만 변경")

# 무기 3계열 — 주인공 고정 5요소 유지, 포즈와 무기만 변경 (기준 = chasa_idle)
WPN = {"bell": ("a brass handbell (yoryeong) held up in the right hand", ["raising the handbell above the shoulder", "shaking the handbell sideways at arm length", "ringing the handbell downward at waist height"]),
       "tri": ("a long wooden trident (samjichang) with three pale blue #BFE8FF prongs", ["pulling the trident back beside the hip, tip forward", "thrusting the trident straight forward at arm length", "drawing the trident back down to the side"]),
       "brush": ("a large registry brush (myeongbu-but) with an ink-soaked black tip and violet #C9B0FF glow", ["raising the brush above the shoulder", "sweeping the brush across in a wide diagonal arc", "flicking the brush so ink drops fly"])}
for w, (desc, poses) in WPN.items():
    for i, pz in enumerate(poses, 1):
        add(f"characters/chasa_{w}{i}", f"{CHASA}, {pz}, weapon: {desc}", "characters/chasa_idle", "무기·포즈만 변경")
FXW = {"fx_bell": "expanding golden concentric sound rings lying flat on the ground in 2:1 isometric perspective, white center glow",
       "fx_trident": "three parallel pale blue #BFE8FF thrust streaks with a white chevron tip, side-on, flat vector glow",
       "fx_brush": "a single bold black ink brush stroke arc with violet #C9B0FF glow edges and a few ink droplets"}
for k, d in FXW.items():
    for f in range(3):
        add(f"fx/{k}_{f}", f"game effect sprite frame {f+1} of 3: {d}", f"fx/{k}_0" if f else "", "프레임 진행만 변경")

pack = []; missing = []
for m in man:
    key = m["file"][:-4]
    if key not in S:
        missing.append(key); continue
    subj, ref, var = S[key]
    is_ui = key.startswith(("hud/", "icons/"))
    style = STYLE if not is_ui else ("Korean folk dark-fantasy game UI, flat clean vector-like rendering, palette navy #16213E and #0F1729, gold #D4A94E, teal #5FE3C0, red #E85C41, hanji #F3E7D3")
    prompt = f"{subj}. {style}. {BG}. Output canvas {m['w']}x{m['h']} px."
    pack.append({"file": m["file"], "size": [m["w"], m["h"]], "ppu": m["ppu"], "pivot": [m["pivotX"], m["pivotY"]], "tint": m["tint"],
                 "prompt": prompt, "negative": NEG, "reference": (ref + ".png") if ref else "", "change_only": var})
assert not missing, missing
out = os.path.join(ROOT, "assets", "prompts", "higgsfield")
os.makedirs(out, exist_ok=True)
json.dump({"count": len(pack), "rule": "작품명 0개, HEX 직접 명시, 변수 1개씩, 첫 승인 이미지를 레퍼런스로 고정", "items": pack},
          open(os.path.join(out, "PROMPT-PACK.json"), "w"), ensure_ascii=False, indent=1)
print(len(pack), "prompts")
