"""3D 에셋 후보 승인 페이지 생성기. 미리보기 그림은 /mnt/project-files/art/3d-candidates/<id>.(jpg|png)가 있으면 data URI로 넣는다.
이유: 아티팩트는 외부 이미지를 막으므로 그림은 파일 안에 포함해야 한다."""
import os, io, base64, json, html
IMG = "/mnt/project-files/art/3d-candidates"
OUT = "/tmp/claude-0/-home-claude-chasa/180ef1c7-c519-55c2-b260-5b5ae388dc6b/scratchpad/3d_candidates.html"
# id, 구역, 이름, 쓸 곳, 라이선스, 가격, 적합도(1~5), 내용, 주의, 링크
C = [
("q-ubc","동이·인물","Universal Base Characters (Quaternius)","동이 몸 규격(뼈대) 확인용 임시 대역","CC0","무료(표준판)",3,"남녀 기본 몸 6종 + 머리 20종, 휴머노이드 뼈대, 약 1.3만 면. FBX·glTF·OBJ.","흑립·도포는 들어 있지 않아 직접 만들거나 색 입힌 의상으로 대체해야 함.","https://quaternius.com/packs/universalbasecharacters.html"),
("q-ual","애니메이션","Universal Animation Library (Quaternius)","동이·사람형 적의 걷기·뛰기·죽기 동작","CC0","무료(표준판)",4,"동작 120개 이상, 8방향 이동·달리기·죽음·감정표현. 위 기본 몸과 호환.","근접 공격·피격 동작 포함 여부는 페이지에 명시되지 않음(받아서 확인 필요).","https://quaternius.com/packs/universalanimationlibrary.html"),
("mixamo","애니메이션","Mixamo (Adobe)","동이 콤보·구르기·피격 동작 보강","Adobe 약관(로열티 없는 상업 이용)","무료(Adobe 로그인)",4,"사람형 캐릭터와 동작 수천 개, 자동 뼈대 입히기. 게임 제작에 쓸 수 있다고 Adobe FAQ에 적혀 있음.","CC0가 아니라 Adobe 약관. 원본 파일을 공개 저장소에 올리면 안 됨(비공개 전환 후 사용).","https://www.mixamo.com/"),
("q-um","혼·보스","Ultimate Monsters (Quaternius)","잡귀·혼 바탕 몸체 50종(움직임 포함)","CC0","무료",4,"괴물 50종, 모두 애니메이션 포함. FBX·OBJ·Blend·glTF.","귀엽거나 서양식 몬스터가 많아 실루엣을 고르고 색·뿔·가면으로 한국 귀신 느낌을 입혀야 함.","https://quaternius.com/packs/ultimatemonsters.html"),
("q-best","혼·보스","Bestiary – Dungeon Monsters Kit (Quaternius)","보스급 사람형 괴물 7종(무기 포함)","Quaternius 라이선스(상업 이용 가능, CC0 아님)","무료(표준판)",3,"괴물 7종 × 색 3종, 휴머노이드 뼈대. 위 동작 라이브러리와 호환.","동작이 포함되는지 불명확. CC0가 아니므로 라이선스 문구 확인 필요.","https://quaternius.com/packs/bestiarydungeonmonsterskit.html"),
("k-grave","혼·보스","Graveyard Kit (Kenney)","저승·무덤·귀신 분위기 지형과 소품 90점","CC0","무료",4,"무덤·비석·울타리·관·유령 등 90점, 한 팀의 통일된 낮은 면 스타일.","서양 묘지 모양. 비석·봉분 형태는 한국식으로 바꿔 쓰거나 색만 활용.","https://kenney.nl/assets/graveyard-kit"),
("u-voxel","마을·건물","Voxel Korean Traditional Village Pack (Haka, Unity 에셋 스토어)","한옥 마을 전체(유일한 한국 전통 후보)","Unity 에셋 스토어 약관","$19.99(유료)",3,"한국 전통 마을 팩, 6장 스크린샷, 7.4MB, Unity 2019.3 이상.","복셀(네모 블록) 스타일이라 다른 후보와 모양이 안 맞음. 유료이고 공개 저장소 노출 금지. 품목 목록이 페이지에 없음.","https://assetstore.unity.com/packages/3d/environments/voxel-korean-traditional-village-pack-166808"),
("k-dung","마을·건물","Modular Dungeon Kit (Kenney)","명부전·지하 통로 조립 부품 40점","CC0","무료",3,"벽·바닥·계단 등 던전 부품 40점, 변형 2종.","서양 던전 느낌. 붉은 기둥·등불로 색을 바꾸면 명부전 용도로 가능.","https://kenney.nl/assets/modular-dungeon-kit"),
("q-ruins","마을·건물","Ultimate Modular Ruins (Quaternius)","폐당집·무너진 절터","CC0","무료",3,"폐허·던전 조립 부품 90개, 애니메이션 캐릭터와 소품 포함.","서양 유적 모양. 돌담·기단 부품으로 활용.","https://quaternius.com/packs/ultimatemodularruins.html"),
("q-snm","지형·자연","Stylized Nature MegaKit (Quaternius)","솔고개 숲·보릿들 풀밭·바위","CC0","무료(표준판)",4,"나무 40종, 풀·꽃 35종, 바위 27종 등 116개, 질감 포함.","소나무는 전용 모델이 없을 수 있어 가까운 나무를 골라 써야 함.","https://quaternius.com/packs/stylizednaturemegakit.html"),
]
SEC = ["동이·인물","애니메이션","혼·보스","마을·건물","지형·자연","소품·이펙트"]
def img(i):
    for e in ("jpg","png"):
        p=f"{IMG}/{i}.{e}"
        if os.path.exists(p):
            try:
                from PIL import Image
                im=Image.open(p).convert("RGB"); im.thumbnail((720,720)); b=io.BytesIO(); im.save(b,"JPEG",quality=78)
                return "data:image/jpeg;base64,"+base64.b64encode(b.getvalue()).decode()
            except Exception: return ""
    return ""
def card(c):
    i,sec,n,use,lic,price,fit,cont,warn,url=c; im=img(i)
    pic=f'<img src="{im}" alt="{html.escape(n)} 미리보기" loading="lazy">' if im else '<div class="noimg">미리보기 준비 중<br><small>링크에서 확인</small></div>'
    free = "무료" in price and "유료" not in price.split("(")[0]
    dots="".join(f'<i class="{"on" if k<fit else ""}"></i>' for k in range(5))
    lc = "cc0" if lic.startswith("CC0") else "other"
    return f'''<article class="card" id="{i}" data-id="{i}"><div class="pic">{pic}</div><div class="body"><h3>{html.escape(n)}</h3>
<p class="use">{html.escape(use)}</p><div class="tags"><span class="tag {lc}">{html.escape(lic)}</span><span class="tag price">{html.escape(price)}</span></div>
<p class="fit" title="쿼터뷰 한국 저승 톤 적합도"><b>톤 적합도</b> <span class="dots" aria-label="5점 만점에 {fit}점">{dots}</span> {fit}/5</p>
<p class="cont">{html.escape(cont)}</p><p class="warn"><b>주의</b> {html.escape(warn)}</p>
<p class="lnk"><a href="{url}" target="_blank" rel="noopener">공식 페이지 열기</a></p>
<div class="vote" role="group" aria-label="승인 선택"><button data-v="approve">승인</button><button data-v="hold">보류</button><button data-v="drop">제외</button></div></div></article>'''
secs="".join(f'<section><h2>{s}</h2><div class="grid">{"".join(card(c) for c in C if c[1]==s)}</div></section>' for s in SEC)
ids=json.dumps([c[0] for c in C])
page=open(os.path.join(os.path.dirname(__file__),"3d_candidates_template.html"),encoding="utf-8").read().replace("{{SECTIONS}}",secs).replace("{{IDS}}",ids).replace("{{N}}",str(len(C)))
open(OUT,"w",encoding="utf-8").write(page); print(OUT,len(page)//1024,"KB", sum(1 for c in C if img(c[0])),"imgs")
