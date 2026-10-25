"""장례·제사 애도객 10모델(상주·아내·막내딸·상여꾼 둘·만장잡이·이웃 아낙·조문 노인·어린 상제·무명 올리는 장터 사람).
실행: python3 mourners.py [--sheets] [id ...]
왜 이렇게: 시나리오(FUNERAL-SEQUENCE §3)가 요구하는 사람 — 상여꾼 여덟, 요령잡이(=갑술 영감 N105), 만장, 상주(아들), 아내, 막내딸, 이웃 — 을
 마을 사람(npcs.py)과 같은 16뼈 틀로 만들어 유니티 컨트롤러 하나를 같이 쓰게 한다. 상여꾼 여덟은 '상여꾼 A·B' 두 모양을 번갈아 복제해서 만든다.
 - 상복은 삼베색(회갈 베옷 #BDB195 / 흰 소복 #E3DCC8)이고, 평소 마을 사람의 선명한 색과 한눈에 구별된다. 주황은 파혼 전용이라 쓰지 않는다.
 - 나이·신분은 실루엣으로 읽힌다: 상주=굴건(높은 삼베 관)+지팡이, 아내=풀어헤친 머리, 딸=땋은 머리+품에 안은 짚신, 상여꾼=어깨의 긴 채, 만장잡이=머리 위로 솟은 깃발.
 - 애도객은 차사를 보지 못하므로 놀람(Startle)·말하기·일하기 동작이 없다. 대신 Weep(서서 울기)·MournStand(고개 숙이고 서기)·Wail(주저앉아 울기)이 있다.
 - 좌표·단위·뼈 이름은 npcs.py와 같다(m, 원점=발바닥, 정면 -Y)."""
import sys, os, json, math
sys.path.insert(0, os.path.dirname(__file__))
from lib3d import *
import anim
import npcs
import npc_motion as nm

HAIR_ = "#14141F"
HEMP = "#BDB195"      # 상주 베옷(굵은 삼베)
MOURN_W = "#E3DCC8"   # 소복(흰 무명, 약간 누런)
HEMP_L = "#CFC6B0"    # 상여꾼 적삼

# ── 소품(서 있는 사람에게 끼우는 것). 규칙은 npcs.py와 같다: (K_, H, add) ────────────────────────
def pr_gulgeon(K_, H, add):
    """굴건(상제가 쓰는 삼베 관) + 수질(머리에 두른 새끼 테). 높고 각진 관이 머리 위로 솟아 '상주'가 한눈에 읽힌다."""
    add("Head", K_.cyl("gulgeon", 0.15, 0.1, 0.24, (0, 0, 1.62), HEMP_L, 8), K_.box("gTop", (0.2, 0.2, 0.04), (0, 0.0, 1.86), HEMP),
        K_.cyl("sujil", 0.145, 0.145, 0.035, (0, 0, 1.64), "thatch", 8), K_.box("hemp1", (0.025, 0.03, 0.2), (0.14, -0.02, 1.52), "thatch"), K_.box("hemp2", (-0.025, 0.03, 0.2), (-0.14, -0.02, 1.52), "thatch"))

def pr_sangjang(K_, H, add):
    """상장(喪杖): 상주가 짚는 지팡이. 어머니 상은 오동, 아버지 상은 대나무. 키보다 한 뼘 아래까지 오는 굵은 막대에 위가 둥글다."""
    x, y, z = H["R"]
    add("Hand.R", K_.cyl("sjStaff", 0.032, 0.03, 1.2, (x, y - 0.03, 0.0), "#9C8B68", 6), K_.sph("sjTop", 0.045, (x, y - 0.03, 1.2), "#9C8B68", 6, 4), K_.box("sjCloth", (0.04, 0.03, 0.22), (x + 0.02, y - 0.03, 1.02), HEMP_L))

def pr_hemp_waist(K_, H, add):
    """요질(허리에 두른 삼 새끼띠) 두 가닥이 늘어진 모양. 상복임을 알려 준다."""
    add("Hips", K_.cyl("yojil", 0.225, 0.225, 0.06, (0, 0, 0.98), "thatch", 8), K_.box("yojilTail", (0.04, 0.04, 0.34), (0.09, -0.225, 0.68), "thatch"), K_.box("yojilTail2", (0.04, 0.04, 0.28), (0.14, -0.225, 0.72), "thatch"))

def pr_loose_hair(K_, H, add):
    """풀어헤친 머리(아내의 곡): 쪽을 풀어 어깨 아래까지 흘러내린다. 머리 위 쪽·비녀가 없다는 것이 소복 입은 '미망인'의 표시."""
    hc = "#14141F"; z = 1.58
    add("Head", K_.sph("looseCap", 0.138, (0, 0.02, z + 0.04), hc, 7, 4, (1, 1, 0.82)), K_.box("lockC", (0.2, 0.06, 0.62), (0, 0.13, z - 0.28), hc), K_.box("lockL", (0.05, 0.07, 0.5), (0.12, 0.08, z - 0.22), hc, rot=(0, 0, -0.12)), K_.box("lockR", (0.05, 0.07, 0.46), (-0.12, 0.08, z - 0.2), hc, rot=(0, 0, 0.12)))

def pr_white_headband(K_, H, add):
    """흰 머리수건: 이마를 감은 흰 띠와 뒤에서 묶은 매듭. 소복 차림 여자들의 표시."""
    z = 1.58
    add("Head", K_.cyl("hband", 0.14, 0.14, 0.05, (0, 0, z + 0.05), "hanji", 8), K_.box("hknot", (0.07, 0.05, 0.07), (0, 0.15, z + 0.07), "hanji"), K_.box("htail", (0.04, 0.02, 0.2), (0.04, 0.17, z - 0.08), "hanji", rot=(0, 0.2, 0)))

def pr_bier_pole_r(K_, H, add):
    """상여 채(오른 어깨 쪽): 앞뒤로 긴 막대 한 토막이 어깨에 얹히고, 멜빵 줄이 어깨에서 내려온다. 여덟 명이 줄지어 있으면 한 줄로 이어 보인다."""
    add("Chest", K_.box("pole", (0.09, 2.6, 0.09), (-0.26, 0.0, 1.5), "wood_dark"), K_.box("sling", (0.04, 0.04, 0.3), (-0.26, 0.0, 1.35), "thatch"), K_.box("slingB", (0.05, 0.05, 0.05), (-0.26, 0.0, 1.2), "#B5473F"))

def pr_bier_pole_l(K_, H, add):
    """상여 채(왼 어깨 쪽): 위와 같은데 반대쪽 어깨."""
    add("Chest", K_.box("pole", (0.09, 2.6, 0.09), (0.26, 0.0, 1.5), "wood_dark"), K_.box("sling", (0.04, 0.04, 0.3), (0.26, 0.0, 1.35), "thatch"), K_.box("slingB", (0.05, 0.05, 0.05), (0.26, 0.0, 1.2), "#B5473F"))

def pr_manjang(K_, H, add):
    """만장(輓章): 키의 두 배쯤 되는 깃대에 흰 천을 길게 늘어뜨린 기. 죽은 이를 기리는 글(짙은 먹 줄)이 천에 세로로 적혀 있다. 머리 위로 솟아 멀리서도 행렬이 읽힌다."""
    x, y, z = H["R"]
    add("Hand.R", K_.cyl("mjPole", 0.022, 0.018, 3.1, (x, y - 0.03, 0.0), "wood", 5), K_.box("mjTop", (0.4, 0.03, 0.04), (x, y - 0.03, 2.95), "wood"),
        K_.box("mjCloth", (0.34, 0.012, 1.5), (x, y - 0.03, 2.18), "hanji"), K_.box("mjBand", (0.34, 0.014, 0.08), (x, y - 0.03, 2.9), "#2A2A38"),
        *[K_.box(f"mjInk{i}", (0.05, 0.016, 0.16), (x, y - 0.034, 2.7 - 0.22 * i), "#2A2A38") for i in range(4)])

def pr_shoes_bundle(K_, H, add):
    """아버지 짚신 한 켤레를 가슴에 안은 모습: 짚신 두 짝이 가슴 앞에 포개져 있다(막내딸)."""
    add("Chest", K_.box("shoeA", (0.1, 0.24, 0.07), (0.05, -0.28, 1.14), "thatch", rot=(0.2, 0, 0.1)), K_.box("shoeB", (0.1, 0.24, 0.07), (-0.05, -0.29, 1.2), "thatch", rot=(0.2, 0, -0.1)), K_.box("shoeCord", (0.16, 0.03, 0.03), (0, -0.3, 1.15), "#B5473F"))

def pr_cup(K_, H, add):
    """술잔과 받침(노제): 오른손에 들린 흰 사기 잔."""
    x, y, z = H["R"]
    add("Hand.R", K_.cyl("cup", 0.045, 0.03, 0.06, (x, y - 0.16, z + 0.06), "hanji", 7), K_.cyl("cupBase", 0.07, 0.07, 0.015, (x, y - 0.16, z + 0.05), "wood", 8))

def pr_tteok_basket(K_, H, add):
    """떡 광주리: 왼팔에 걸친 대바구니와 흰 보자기(이웃 아낙이 상여꾼에게 나르는 떡)."""
    x, y, z = H["L"]
    add("Hand.L", K_.cyl("tkBasket", 0.16, 0.2, 0.15, (x, y - 0.08, z - 0.16), "thatch", 8), K_.cyl("tkCloth", 0.18, 0.14, 0.05, (x, y - 0.08, z - 0.02), "hanji", 8))

def pr_cloth_roll(K_, H, add):
    """무명 한 필: 두 팔에 안은 흰 천 두루마리. 외상 지운 포목전 문 앞에 하나씩 놓고 가는 문상의 표시."""
    add("Chest", K_.cyl("roll", 0.07, 0.07, 0.34, (0.0, -0.3, 1.0), "hanji", 8, rot=(0, math.pi / 2, 0.0)), K_.box("rollBand", (0.05, 0.14, 0.14), (0.0, -0.3, 1.02), "#B5473F"))

NEW_PROPS = (pr_gulgeon, pr_sangjang, pr_hemp_waist, pr_loose_hair, pr_white_headband, pr_bier_pole_r, pr_bier_pole_l, pr_manjang, pr_shoes_bundle, pr_cup, pr_tteok_basket, pr_cloth_roll)
for f in NEW_PROPS: npcs.PROPS[f.__name__[3:]] = f

# ── 걸음: 장례 행렬은 느리고 고개를 숙이고 걷는다 ───────────────────────────────────────────
PROC = dict(sl=0.40, N=84, lean=4, swing=0.3, head_hn=14)                                      # 행렬 걸음(0.57 m/s)
CARRY = dict(sl=0.40, N=84, lean=2, hold={"R": (60, 10, 78), "L": (60, 10, 78)}, swing=0.2, bob_extra=0.010, head_hn=4)   # 어깨에 채를 메고 박자 맞춰
HUG = dict(sl=0.38, N=84, lean=4, hold={"R": (78, -10, 112), "L": (78, -10, 112)}, swing=0.2, head_hn=12)                  # 짚신 안고

def M(id, name, tmpl, **kw): return dict(id=id, name=name, tmpl=tmpl, mourner=True, **kw)
SPECS_M = [
 M("M01", "맏상주(지팡이)", "상주(남, 굴건제복)", sex="m", k=1.0, skin="skin", top=HEMP, bottom=HEMP, robe=HEMP, sash="thatch", haircol=HAIR_, hair="none", props=["gulgeon", "sangjang", "hemp_waist"], walk={**PROC, "hold": {"R": (15, 6, 20)}}, note="행렬 앞의 상주. 굴건·베옷·상장(지팡이)·허리 새끼띠"),
 M("M01b", "맏상주(노제 술잔)", "상주(남, 굴건제복)", sex="m", k=1.0, skin="skin", top=HEMP, bottom=HEMP, robe=HEMP, sash="thatch", haircol=HAIR_, hair="none", props=["gulgeon", "hemp_waist", "cup"], walk=PROC, note="노제에서 술잔을 올리는 상주(지팡이는 내려놓음)"),
 M("M02", "상주 아내", "미망인(소복)", sex="f", k=0.92, skin="skin", top=MOURN_W, bottom=MOURN_W, ribbon="hanji", haircol=HAIR_, hair="none", skirt_w=0.42, props=["loose_hair", "white_headband"], walk=PROC, note="풀어헤친 머리에 흰 수건. 상여 끝을 붙잡고 따라 나온다"),
 M("M03", "막내딸", "10대 딸(소복)", sex="f", k=0.82, skin="skin", top=MOURN_W, bottom=MOURN_W, ribbon="hanji", haircol=HAIR_, hair="braid", daenggi=MOURN_W, skirt_w=0.38, props=["shoes_bundle"], walk=HUG, note="울지 않고 아버지 짚신을 품에 안는다"),
 M("M04a", "상여꾼 A", "상여꾼(건장)", sex="m", k=1.0, wide=1.1, skin="#C49A78", top=HEMP_L, bottom=HEMP_L, sash="#2A2A38", haircol=HAIR_, hair="topknot", hat=("headcloth", "hanji"), props=["bier_pole_r"], walk=CARRY, note="상여 채를 오른 어깨에 멘 상여꾼(여덟 명 중 짝수 자리)"),
 M("M04b", "상여꾼 B", "상여꾼(젊음)", sex="m", k=0.97, wide=1.05, skin="#C49A78", top="#C9BFA6", bottom="#9C9078", sash="#B5473F", haircol=HAIR_, hair="topknot", hat=("headcloth", "hanji"), props=["bier_pole_l"], walk=CARRY, note="왼 어깨에 멘 상여꾼(여덟 명 중 홀수 자리)"),
 M("M05", "만장잡이", "청년(만장)", sex="m", k=0.95, skin="skin", top=HEMP_L, bottom=HEMP_L, sash="thatch", haircol=HAIR_, hair="topknot", hat=("headcloth", "hanji"), props=["manjang"], walk={**PROC, "hold": {"R": (62, 8, 80)}}, note="상여 뒤를 따르며 만장을 든다"),
 M("M06", "이웃 아낙", "아낙(중년, 소복 차림)", sex="f", k=0.94, skin="#C49A78", top="#D8D0C0", bottom="#8C8C84", ribbon="hanji", haircol=HAIR_, hair="bun", skirt_w=0.48, props=["white_headband", "tteok_basket"], walk={**PROC, "hold": {"L": (30, 6, 55)}}, note="상여꾼에게 떡을 나르는 이웃 아낙"),
 M("M07", "조문 노인", "노인(흰 도포)", sex="m", k=0.93, skin="old_skin", top="hanji", bottom="hanji", robe=MOURN_W, sash="#8E8A84", haircol="#D8D0C0", hair="none", beard="#D8D0C0", hunch=True, hat=("gat", "hat"), props=["cane"], walk={**PROC, "sl": 0.34, "N": 90, "hold": {"R": (22, 6, 15)}}, note="행렬을 따라 걷는 마을 어른. 흰 도포·검은 갓·지팡이"),
 M("M08", "어린 상제", "아이(상복)", sex="m", k=0.68, child=True, skin="skin", top=HEMP, bottom=HEMP, sash="thatch", haircol=HAIR_, hair="none", props=["gulgeon"], walk={**PROC, "sl": 0.34, "N": 60, "swing": 0.5}, note="굴건이 큰 어린 상제(죽음을 직접 그리지 않고 상복으로만 보인다)"),
 M("M09", "무명 올리는 사람", "장터 사람(문상)", sex="m", k=1.0, skin="#C49A78", top="#8A7A60", bottom="#5A4630", sash="#586080", haircol=HAIR_, hair="topknot", hat=("headcloth", "#D8D0C0"), props=["cloth_roll"], walk={**PROC, "hold": {"R": (70, -6, 100), "L": (70, -6, 100)}}, note="외상을 지워 준 포목전 문 앞에 무명 한 필을 놓는 사람(S-020 변주)"),
]
nm.ROLE.update({"M01": ["Bow", "Wail"], "M01b": ["PourCup", "Bow", "Wail"], "M02": ["Wail", "Bow"], "M03": ["HugShoes"], "M04a": [], "M04b": [], "M05": ["HoldFlag"], "M06": [], "M07": ["Bow"], "M08": [], "M09": ["Bow"]})

def build_all(want=None):
    res = []
    for s in SPECS_M:
        if want and s["id"] not in want: continue
        r = npcs.build_one(s); res.append(r); print(r["id"], r["name"], "키", r["height_m"], "삼각형", r["tris"], r["verify"]["joints"], "뼈", r["verify"]["animations"])
    if not want:
        json.dump({"fps": anim.FPS, "note": "장례·제사 애도객. 마을 사람과 같은 16뼈 틀. 놀람·말하기·일하기 동작은 없다(차사를 보지 못한다).", "mourners": res},
                  open(os.path.join(npcs.OUT, "npcs", "_mourner_manifest.json"), "w"), ensure_ascii=False, indent=1)

def sheets():
    from PIL import Image
    reset(); anim.setup_scene()
    for i, s in enumerate(SPECS_M):
        o, arm, cover = npcs.make(s); o.parent.location = ((i % 6) * 1.5, -(i // 6) * 3.4, 0)
    setup_render(10.4, (1.5 * 2.5, -1.7, 0.95), elev=34, size=(1500, 940), ground_size=30)
    bpy.context.scene.cycles.samples = 24; render(os.path.join(npcs.OUT, "previews", "mourners_all.png"))
    from PIL import Image
    def strip(sid, clipn, fr, ortho=3.0, cz=0.95):
        """앞모습·옆모습 두 줄로 같은 프레임을 찍는다(옆에서 봐야 숙임·주저앉음·상여 채가 보인다)."""
        s = [x for x in SPECS_M + npcs.SPECS if x["id"] == sid][0]; rows = []
        for yaw in (0, 90):
            reset(); anim.setup_scene(); o, arm, cover = npcs.make(s)
            for name, c in npcs.clips(s, cover).items(): anim.clip(arm, name, c[0], c[1])
            o.parent.rotation_euler = (0, 0, math.radians(yaw))
            setup_render(ortho, (0, 0, cz), elev=20, size=(260, 330), ground_size=10)
            rows.append(Image.open(anim.sheet(arm, clipn, fr, os.path.join(npcs.OUT, "previews", f"_tmp_{sid}_{clipn}_{yaw}"), cell=(260, 330))).convert("RGB"))
        W = Image.new("RGB", (rows[0].width, 660)); W.paste(rows[0], (0, 0)); W.paste(rows[1], (0, 330))
        p = os.path.join(npcs.OUT, "previews", f"anim_mourn_{sid}_{clipn}.png"); W.save(p)
        for yaw in (0, 90): os.remove(os.path.join(npcs.OUT, "previews", f"_tmp_{sid}_{clipn}_{yaw}.png"))
        print(p)
    for a in (("M02", "Wail", [0, 10, 18, 28, 40], 2.6, 0.7), ("M06", "Weep", [0, 15, 30, 45, 60], 2.8, 0.95), ("M04a", "Walk", [0, 10, 21, 31, 42], 3.0, 0.95), ("M03", "HugShoes", [0, 30, 60, 90], 2.8, 0.8), ("M01b", "PourCup", [0, 24, 50, 82, 112, 130], 3.0, 0.95), ("M01", "MournStand", [0, 30, 100, 130], 3.0, 0.95)):
        strip(*a)

if __name__ == "__main__":
    want = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--sheets" in sys.argv: sheets()
    else: build_all(want)
