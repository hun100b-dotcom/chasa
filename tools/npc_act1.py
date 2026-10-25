# 1막(① 솔고개 · ② 검은여울) 산 사람 NPC 시간표 + 엿듣기 + 보스 낮 단서 생성기
import json
import os
OUT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','docs','narrative','npc_act1.json')

def slot(time, zone, place, line=None, half=None, verb=None, clue=None, fact=None, note=None):
    s={"time":time,"zone":zone,"place":place}
    if verb: s["verb"]=verb
    if line: s["line"]=line
    if half: s["line_half"]=half
    s["clue"]=clue
    if fact: s["fact_hint"]=fact
    if note: s["note"]=note
    return s

npcs=[
 # ───── ① 솔고개 ─────
 {"id":"N-101","name":"당할미","region":1,"role":"서낭당 무녀. 차사를 보지 못하고 찬 기운만 느낀다(플레이어의 어머니 — 화면에서 말하지 않음)","unlock_night":1,
  "schedule":[
   slot("새벽","Hub","서낭당 나무 아래",verb="지켜보기",note="이름 없는 기도. 이름 자리에서 늘 숨이 끊긴다. 엿듣기 대상 아님(말이 아니라 기도)"),
   slot("낮","Hub","서낭당 나무 아래",line="부채 살이 또 하나 나갔네. 열두째는 끝내 못 펴 보셨지.",half="부채 살이 또 하나…",verb="지켜보기",clue="B02-D1",note="살 부러진 부채를 펼쳐 본다(월화의 부채). 지켜보기 단서"),
   slot("낮","Hub","서낭당 돌무더기 곁",line="예전 차사님은 갓끈이 붉었는데…",half="예전 차사님은…",verb="엿듣기",clue="B12-D1",note="② 검은여울이 열린 뒤(밤 13 이후)부터. 허공에 대고 하는 혼잣말"),
   slot("저녁","Hub","서낭당 가지(명부가 걸림)",line="…또 오셨소. 추운 걸 보니.",note="해 질 녘 명부를 내려놓는다. 1밤 고정 대사, 그 뒤로는 말 없이 명부만"),
   slot("밤","Village","당할미 집",note="집 안. 엿듣기 없음")]},
 {"id":"N-102","name":"순임","region":1,"role":"나루 영감(도씨 뱃사공)의 손녀. 줄배를 맨다","unlock_night":4,
  "schedule":[
   slot("새벽","Ravine","물막이 골 나루 계단",note="장대에 등을 단다"),
   slot("낮","Hub","서낭당 나무(천을 묶는다)",line="할아버지 허리춤 엽전 꾸러미가 끝내 안 나왔어요. 그 돈은 남의 돈이라 손대면 안 된다고 하셨는데.",half="할아버지 허리춤 엽전 꾸러미가…",verb="엿듣기",clue="B01-D3",note="당할미와 이야기한다. 업 30 이상이면 '갑자기 춥네' 하고 말없이 떠난다(BOSS-01)"),
   slot("저녁","Ravine","물막이 골 줄배",note="줄배를 묶는다"),
   slot("밤","Village","도씨네 집",note="엿듣기 없음")]},
 {"id":"N-103","name":"윤 소사네 아들","region":1,"role":"윤 소사(S-002)와 윤 영감(B-21)의 아들. 제사를 지낸다","unlock_night":4,
  "schedule":[
   slot("낮","Village","윤 소사네 마당 제사상",line="아버지는 그날 나루에서 배 기다리다…",verb="지켜보기",clue="B01-D1",note="제사상에 뱃삯만큼의 엽전 다섯 닢. 윤 소사를 천도해 장례를 봤다면 위패가 둘. 업 10 이상이면 말을 멈추지만 위패와 엽전은 보이므로 단서는 반쪽 문장으로 기록"),
   slot("저녁","Village","윤 소사네 마당",note="상을 치운다")]},
 {"id":"N-104","name":"복남·언년이·삼돌이","region":1,"role":"마을 아이들. 노래놀이를 한다","unlock_night":7,
  "schedule":[
   slot("낮","Ravine","물막이 골 주막 터",line="열두 잔에 이름 열둘, 한 잔은 엎어졌네.",half="열두 잔에 이름 열둘…",verb="엿듣기",clue="B02-D2",note="노래 도중 어른이 '그 노래 하지 마라' 하고 끊는다(소설 10장). 끊겨도 단서는 인정"),
   slot("저녁","Village","우물가",line="삼돌아, 밥 먹어라!",note="삼돌이 어미가 부르는 소리(소설 12장). 단서 아님, 분위기")]},
 {"id":"N-105","name":"갑술 영감","region":1,"role":"상여 선소리꾼","unlock_night":2,
  "schedule":[
   slot("낮","Village","마을 어귀 정자",line="올해만 상여를 몇 번 멨나. 소리할 목이 남아나질 않아.",half="올해만 상여를…",verb="엿듣기",clue=None,fact="F2",note="마을 소문. 업 60 이상이면 닫힘"),
   slot("저녁","Village","정자",note="담뱃대를 턴다")]},
 {"id":"N-106","name":"곱단네","region":1,"role":"마을 아낙","unlock_night":2,
  "schedule":[
   slot("낮","Village","우물가",line="나루가 끊기고는 강 건너 장엘 못 가. 소금이 귀해.",half="나루가 끊기고는…",verb="엿듣기",clue=None,fact="F3",note="간난이와 함께 있다")]},
 {"id":"N-107","name":"간난이","region":1,"role":"마을 아낙","unlock_night":2,
  "schedule":[
   slot("낮","Village","우물가",line="할미는 그 밤 뒤로 새벽마다 나무 밑이여. 무엇을 비는지는 몰라.",half="할미는 그 밤 뒤로…",verb="엿듣기",clue=None,fact="F8",note="아들 이야기를 직접 하지 않는다. F8의 그림자만")]},
 {"id":"N-108","name":"덕만","region":1,"role":"홍 소장수(S-008)의 아들. 왼 눈썹에 흉","unlock_night":2,
  "schedule":[
   slot("낮","Field","보릿들 둑",line="아버지 상에는 아무도 안 왔어. 부르러 간 사람이 없었으니까.",half="아버지 상에는…",verb="엿듣기",clue=None,fact="F1",note="홍 소장수(인 없음)를 천도했다면 다음 낮엔 이 줄 대신 둑에 앉아 소 고삐를 감는다")]},
 {"id":"N-109","name":"용득","region":1,"role":"박돌쇠(S-001)의 맏아들. 대장간을 잇는다","unlock_night":1,
  "schedule":[
   slot("새벽","Village","박돌쇠네 대장간",note="풀무에 불을 넣는다. 박돌쇠를 파혼했다면 대문에 조등만, 풀무는 식은 채"),
   slot("낮","Village","대장간",line="아버지 망치는 그대로 둬라. 손잡이에 손 자국이 아직 있다.",half="아버지 망치는…",verb="엿듣기",clue=None,note="금순(막내딸)에게 하는 말. 박돌쇠 천도 뒤에만")]},
 {"id":"N-110","name":"등짐장수 둘(득보와 동무)","region":1,"role":"검은여울에서 넘어온 등짐장수. 둘째 관할로 이어지는 복선","unlock_night":6,
  "schedule":[
   slot("낮","Hub","서낭당 고개 고갯마루",line="검은여울 장이 반도 안 섰더구먼. — 묻지 마. 거기선 묻는 놈이 매 맞는다더라.",half="검은여울 장이…",verb="엿듣기",clue=None,fact="F10",note="앞줄은 득보, 뒷줄은 동무. 소설 7장")]},
 # ───── ② 검은여울 ─────
 {"id":"N-201","name":"득보","region":2,"role":"등짐장수. 장날 '역병' 말을 했다가 사령에게 끌려간다","unlock_night":13,
  "schedule":[
   slot("낮","Market","장터거리 장마당",line="역병 없었다는데 무덤골 새 무덤은 왜 많나.",half="역병 없었다는데…",verb="엿듣기",clue="B03-D1",note="말한 직후 사령(N-207)이 끌고 간다. 이후 낮엔 옥 앞 → 풀려난 다음 낮부터 장마당에 다시 선다"),
   slot("밤","Yamen","동헌 뒤 옥",line="예.",note="옥지기가 '열넷' 하고 부르면 대답한다(끌려간 그 밤만). 이름혼 '이름 넷'과 맞서는 장면")]},
 {"id":"N-202","name":"은실","region":2,"role":"서 의원(서인보)의 딸. 장터에서 약방을 한다","unlock_night":13,
  "schedule":[
   slot("낮","Plague","역병막 빈 움막 섬돌",verb="지켜보기",clue="B03-D2",note="빈 움막마다 약을 달여 둔 사발을 놓는다. 의원 움막 쪽은 끝내 보지 않는다. 지켜보기 단서(낮 이른 때)"),
   slot("낮","Market","장터 약방",line="감초는 위 칸 것만 드려요. 아래 칸은 손대지 마세요.",half="감초는 위 칸…",verb="엿듣기",clue=None,note="당할미가 뿌리를 팔고 감초를 사 갈 때. 단서 아님(명단 위치 복선)"),
   slot("저녁","Market","약방",note="문을 닫는다")]},
 {"id":"N-203","name":"섭섭이","region":2,"role":"주모 끝순(S-021)의 딸. 주막을 잇는다","unlock_night":13,
  "schedule":[
   slot("낮","Market","장터 주막 부엌",line="엄마도 고뿔이랬어. 다들 고뿔이래.",half="엄마도 고뿔…",verb="엿듣기",clue=None,fact="F10",note="부엌 문설주에 '고뿔 조심' 종이. 끝순 장례 뒤에는 종이를 뗀 자국만"),
   slot("저녁","Market","주막",note="등을 건다")]},
 {"id":"N-204","name":"꼭지·차돌이","region":2,"role":"엿장수 판쇠(S-019)를 따르던 장터 아이들","unlock_night":13,
  "schedule":[
   slot("낮","Market","장터 엿판 자리",line="판쇠 아재 가위 소리가 안 나. 사흘째야.",half="판쇠 아재 가위…",verb="엿듣기",clue=None,note="판쇠 천도 뒤에는 그 자리에 큰 가위가 놓이고 아이들이 번갈아 쳐 본다")]},
 {"id":"N-205","name":"노경수 어른 손주","region":2,"role":"아전 노씨(S-022, 노경수)의 손주. 아이","unlock_night":14,
  "schedule":[
   slot("낮","Yamen","동헌 터 탄 문서함 곁",verb="지켜보기",clue=None,note="막대기로 흙에 글자를 따라 쓴다. 골목에서 '경수 어른 손주야, 거기 들어가지 마라' 소리. 시즌 3 B-26 엿듣기(손자의 회상)로 이어짐")]},
 {"id":"N-206","name":"옥지기","region":2,"role":"동헌 뒤 옥을 지키는 산 사람. 옥사장 강쇠(S-023)와 다른 사람","unlock_night":14,
  "schedule":[
   slot("밤","Yamen","동헌 뒤 둥근 돌담 옥",line="열하나, 열둘, 열셋… 열넷. 물 먹어라.",half="열하나, 열둘…",verb="엿듣기",clue=None,fact="F13",note="옥에 든 사람을 번호로 부른다. 밤에도 들리는 몇 안 되는 산 사람 말"),
   slot("낮","Yamen","옥문 앞",note="졸고 있다")]},
 {"id":"N-207","name":"사령","region":2,"role":"관아 사령(이름 없음)","unlock_night":13,
  "schedule":[
   slot("저녁","Yamen","객사 앞 방",line="고뿔로 죽은 이는 사흘 안에 묻으라.",half="고뿔로 죽은 이는…",verb="엿듣기",clue=None,fact="F10",note="방을 읽는다"),
   slot("밤","Plague","역병막 어귀",line="장마 걷히면 거적이고 움막이고 다 태운단다.",half="장마 걷히면…",verb="엿듣기",clue=None,note="밤 순라. 역병막이 열린 뒤(밤 16~)")]},
]

boss_clues={
 "B-01":{"name":"나루 영감","sentence":"건네지 못한 마지막 손님","zone_opens":"Ravine (밤 4~6)","clues":[
   {"id":"B01-D1","verb":"지켜보기","time":"낮","zone":"Village","place":"윤 소사네 제사상","npc":"N-103","what":"엽전 다섯 닢과 위패"},
   {"id":"B01-D2","verb":"만져 보기","time":"낮","zone":"Ravine","place":"물막이 골 갈대 속 부러진 삿대","npc":None,"what":"칼금 열한 개, 열두 번째는 반만"},
   {"id":"B01-D3","verb":"엿듣기","time":"낮","zone":"Hub","place":"서낭당 나무","npc":"N-102","what":"순임의 말"},
   {"id":"B01-D4","verb":"밤 대체","time":"밤","soul":"S-010","what":"곽 뱃꾼 천도 기억"}]},
 "B-02":{"name":"월화","sentence":"끝내지 못한 열두 거리","zone_opens":"Shrine (밤 7~10)","clues":[
   {"id":"B02-D1","verb":"지켜보기","time":"낮","zone":"Hub","place":"서낭당 나무 아래","npc":"N-101","what":"당할미가 펼쳐 보는 살 부러진 부채"},
   {"id":"B02-D2","verb":"엿듣기","time":"낮","zone":"Ravine","place":"물막이 골 주막 터","npc":"N-104","what":"아이들 노래"},
   {"id":"B02-D3","verb":"만져 보기","time":"낮","zone":"Shrine","place":"폐당집 굿상","npc":None,"what":"엎어진 열두째 잔"},
   {"id":"B02-D4","verb":"밤 대체","time":"밤","soul":"S-014","what":"신딸 옥이 천도 기억"}]},
 "B-03":{"name":"서 의원(서인보)","sentence":"지운 이름들","zone_opens":"Plague (밤 16~20)","clues":[
   {"id":"B03-D1","verb":"엿듣기","time":"낮","zone":"Market","place":"장마당","npc":"N-201","what":"득보의 소문"},
   {"id":"B03-D2","verb":"지켜보기","time":"낮","zone":"Plague","place":"빈 움막 섬돌","npc":"N-202","what":"은실이 약사발을 놓는 모습"},
   {"id":"B03-D3","verb":"만져 보기","time":"낮","zone":"Yamen","place":"동헌 터 탄 문서함","npc":None,"what":"그은 줄들 끝에 '의원 서○○ 순직' 한 줄만(이름 두 자는 불에 먹힘) 반듯한 종이 한 장"},
   {"id":"B03-D4","verb":"밤 대체","time":"밤","soul":"S-036","what":"의원의 제자(태석) 천도 기억"}]},
 "B-12":{"name":"흑월 차사(2차, ⑥ 성문 밖)","sentence":"(1막 범위 밖 — 여기엔 ① 서낭당 단서 하나만)","zone_opens":"⑥","clues":[
   {"id":"B12-D1","verb":"엿듣기","time":"낮","zone":"Hub","place":"서낭당 돌무더기 곁","npc":"N-101","what":"당할미 혼잣말 '갓끈이 붉었는데'"}],
   "note":"나머지 셋은 ⑥ 데이터에서. B-04(무덤골 1차)는 처결이 없어 단서 없음"}
}

data={
 "_설명":"1막(① 솔고개 · ② 검은여울) 산 사람 NPC 시간표와 엿듣기 대사. 서사 확정 2026-10-25. 이름은 SCENARIO·soul_memories.json·소설 GAME-MAP과 대조함. 산 사람은 차사를 보지 못한다(WORLD-BIBLE §5-1).",
 "_version":1,
 "clock":{"day_minutes":40,"slots":{"새벽":{"code":"Dawn","minutes":2},"낮":{"code":"Day","minutes":14},"저녁":{"code":"Dusk","minutes":2},"밤":{"code":"Night","minutes":22}},"source":"LOCKED-DECISIONS 하루 길이(출발값)"},
 "zones":{"Hub":"서낭당 고개","Village":"솔고개 마을","Field":"보릿들","Ravine":"물막이 골","Shrine":"폐당집","Market":"장터거리","Yamen":"동헌 터","Plague":"역병막","Graves":"무덤골"},
 "rules":{
  "boss_clue":"보스마다 단서 4개(낮 3 + 밤 대체 1), 3개 이상이면 천도. 낮 단서 셋은 동사가 모두 다르다",
  "unlock":"보스 단서 자리는 그 보스 구역에 밤에 처음 들어간 다음 낮부터 열린다. unlock_night는 NPC가 처음 나타나는 밤(이야기 기준)",
  "karma":{"10":"엿듣기는 line_half(반쪽 문장)로 기록, 그래도 단서 1개로 인정","30":"보스 엿듣기 단서 닫힘(사람이 '갑자기 춥네' 하고 떠남)","60":"마을 소문(clue가 null인 엿듣기)까지 모두 닫힘"},
  "fact_hint":"fact_hint는 분위기 연결일 뿐 단서(F)를 켜지 않는다. F는 혼의 기억과 보스 천도로만 켜진다",
  "speaker":"모든 대사는 산 사람끼리 하는 말이다. 차사에게 말하지 않는다. 당할미만 허공에 대고 말한다"},
 "npcs":npcs,
 "boss_clues":boss_clues}
json.dump(data,open(OUT,'w',encoding='utf-8'),ensure_ascii=False,indent=1)
print(len(npcs),'npcs')
