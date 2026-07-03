#!/usr/bin/env python3
"""生成 2000 个涵盖所有简谱符号的训练素材"""
import json, os, random
random.seed(42)

def N(pitch, dur, **kw):
    n = {"pitch": pitch, "duration": dur}
    n.update(kw)
    return n

def D(dur): return {"type": "dash", "duration": dur}
def R(dur): return {"pitch": 0, "duration": dur}

def mk_score(title, measures):
    return {"title": title, "key": "C", "timeSignature": {"numerator": 4, "denominator": 4}, "measures": measures}

PITCHES = [1,2,3,5,6]
LYRICS_POOL = "春夏秋冬风花雪月山水云雨星日天地人梦心光影灯火歌行路远近高深清静明亮暖凉红绿黄白青蓝"
LYRICS = list(LYRICS_POOL)
DYN_TEXTS = ["pp","p","mp","mf","f","ff"]

def T_bo(): return [{"type":"boyin"}]
def T_ch(): return [{"type":"chanyin"}]
def T_da(): return [{"type":"dayin"}]
def T_tu(): return [{"type":"tuyin"}]
def T_di(): return [{"type":"dieyin"}]
def T_du(): return [{"type":"dunyin"}]
def T_hu(d): return [{"type":"huayin","slideDirection":d}]
def T_li(d): return [{"type":"liyin","liyinDirection":d}]
def T_yi(p): return [{"type":"yinyin","graceNotes":[p],"graceOctave":0}]

def make_measure(beats=4, use_tech=False, use_slur=False, use_tie=False, use_dyn=False,
                 use_oct=False, use_acc=False, use_rest=False, use_fer=False, use_ten=False, use_dunyin=False,
                 use_dot=False):
    notes = []
    total = 0.0
    while total < beats - 0.01:
        max_rem = beats - total
        choices = []
        if max_rem >= 1.0: choices.extend([1.0, 1.0, 1.0])
        if max_rem >= 0.5: choices.extend([0.5, 0.5, 0.5])
        if max_rem >= 0.25: choices.extend([0.25, 0.25])
        if max_rem >= 2.0: choices.append(2.0)
        if max_rem >= 1.5: choices.append(1.5)
        dur = random.choice(choices)
        total += dur

        is_rest = use_rest and random.random() < 0.1 and dur >= 0.5
        if is_rest:
            notes.append(R(dur))
            continue

        pitch = random.choice(PITCHES)
        kw = {}
        if random.random() < 0.6: kw["lyric"] = random.choice(LYRICS)
        if use_oct and random.random() < 0.15: kw["octave"] = random.choice([-1,1])
        if use_acc and random.random() < 0.08: kw["accidental"] = random.choice(["sharp","flat","natural"])
        if use_slur and random.random() < 0.15: kw["slurId"] = f"s{random.randint(10,999)}"
        if use_tie and random.random() < 0.1: kw["tieId"] = f"t{random.randint(10,999)}"
        if use_dot and use_tie and random.random() < 0.3: kw["dot"] = 1
        if use_tech and random.random() < 0.12:
            t = random.choice(["boyin","chanyin","dayin","tuyin","dieyin","huayin","liyin","yinyin"])
            if t == "boyin": kw["techniques"] = T_bo()
            elif t == "chanyin": kw["techniques"] = T_ch()
            elif t == "dayin": kw["techniques"] = T_da()
            elif t == "tuyin": kw["techniques"] = T_tu()
            elif t == "dieyin": kw["techniques"] = T_di()
            elif t == "huayin": kw["techniques"] = T_hu(random.choice(["up","down"]))
            elif t == "liyin": kw["techniques"] = T_li(random.choice(["up","down"]))
            elif t == "yinyin": kw["techniques"] = T_yi(random.choice(PITCHES))
        if use_dunyin and random.random() < 0.08:
            if "techniques" not in kw: kw["techniques"] = T_du()
        if use_dyn and random.random() < 0.06: kw["dynamic"] = random.choice(DYN_TEXTS)
        if use_ten and random.random() < 0.06: kw["tenuto"] = True
        if use_fer and random.random() < 0.04: kw["fermata"] = True

        notes.append(N(pitch, dur, **kw))
    return notes

def mk_measures(n, beats=4, **opts):
    return [{"notes": make_measure(beats, **opts)} for _ in range(n)]

all_scores = []

# --- 手工精选素材 (9个, score_001~009) ---
all_scores.append(mk_score("节奏型示例", [
    {"notes":[N(5,0.5,lyric="四"),N(3,0.5,lyric="分"),N(1,0.25,lyric="八"),N(2,0.25,lyric="八"),N(3,0.25,lyric="八"),N(5,0.25,lyric="八"),N(6,0.5,lyric="四"),N(5,0.5,lyric="四")]},
    {"notes":[N(1,1,dot=1,lyric="附"),N(1,0.5,lyric="点"),N(2,1,lyric="二"),N(3,0.5,lyric="拍"),D(0.5)]},
    {"notes":[R(0.5),N(5,0.5,lyric="休"),N(3,0.5,lyric="止"),N(2,2,lyric="长"),D(0.5)]},
    {"notes":[N(1,0.25,lyric="十"),N(2,0.25,lyric="六"),N(3,0.25,lyric="十"),N(5,0.25,lyric="六"),N(6,0.5,lyric="八"),N(5,0.5,lyric="八"),N(3,1,lyric="四"),D(0.5)]},
]))
all_scores.append(mk_score("八度与变音", [
    {"notes":[N(5,0.5,octave=1,lyric="高"),N(6,0.5,octave=1,lyric="八"),N(1,0.5,octave=2,lyric="度"),N(5,0.5,lyric="中"),N(3,0.5,lyric="音"),N(1,0.5,lyric="区"),N(6,0.5),N(5,0.5)]},
    {"notes":[N(5,0.5,octave=-1,lyric="低"),N(6,0.5,octave=-1,lyric="八"),N(1,0.5,octave=-1,lyric="度"),N(2,0.5,lyric="低"),N(3,0.5,lyric="音"),N(2,0.5,lyric="区"),N(1,0.5),N(6,0.25,octave=-1),N(5,0.25,octave=-1)]},
    {"notes":[N(5,0.5,accidental="sharp",lyric="升"),N(6,0.5,accidental="sharp",lyric="号"),N(3,0.5,accidental="flat",lyric="降"),N(2,0.5,accidental="flat",lyric="号"),N(1,0.5,accidental="natural",lyric="还"),N(2,0.5,accidental="natural",lyric="原"),N(3,0.5),N(5,0.5)]},
    {"notes":[N(1,1,lyric="低"),N(5,1,octave=-1),N(6,0.5,octave=-1,lyric="高"),N(1,0.5,octave=1),N(2,0.5,octave=1),N(3,0.5,octave=1)]},
]))
all_scores.append(mk_score("波音颤音倚音", [
    {"notes":[N(5,0.5,lyric="波",techniques=T_bo()),N(3,0.5,lyric="音"),N(2,0.5),N(1,0.5,lyric="波",techniques=T_bo()),N(6,0.5,octave=-1,lyric="音"),N(1,0.5,techniques=T_bo()),N(2,0.5,lyric="波"),N(3,0.25,lyric="音"),N(5,0.25,techniques=T_bo())]},
    {"notes":[N(6,0.5,lyric="颤",techniques=T_ch()),N(5,0.5,lyric="音"),N(3,0.5),N(2,0.5,lyric="颤",techniques=T_ch()),N(1,1,techniques=T_ch()),N(5,0.5,lyric="颤"),N(6,0.5,techniques=T_ch())]},
    {"notes":[N(5,0.5,lyric="倚",techniques=T_yi(3)),N(6,0.5,lyric="音"),N(5,0.5),N(3,0.5,lyric="倚",techniques=T_yi(6)),N(2,0.5,lyric="音"),N(1,0.5),N(5,0.25,techniques=T_yi(3)),N(3,0.25),N(2,0.5)]},
    {"notes":[N(1,1,lyric="波",techniques=T_bo()),N(5,0.5,lyric="颤",techniques=T_ch()),N(6,0.5,lyric="倚",techniques=T_yi(3)),N(5,0.5,lyric="波",techniques=T_bo()),N(3,0.5),N(2,0.5),N(1,0.5)]},
]))
all_scores.append(mk_score("滑音历音叠音", [
    {"notes":[N(5,0.5,lyric="上",techniques=T_hu("up")),N(6,0.5,lyric="滑"),N(5,0.5),N(3,0.5,lyric="下",techniques=T_hu("down")),N(2,0.5,lyric="滑"),N(1,0.5),N(6,0.25,octave=-1,techniques=T_hu("up")),N(1,0.25),N(2,0.5)]},
    {"notes":[N(1,0.5,lyric="上",techniques=T_li("up")),N(5,0.5,lyric="历"),N(3,0.5,lyric="音"),N(2,0.5,lyric="下",techniques=T_li("down")),N(1,0.5,lyric="历"),N(6,0.5,octave=-1,lyric="音"),N(1,0.5),D(0.5)]},
    {"notes":[N(5,0.5,lyric="叠",techniques=T_di()),N(3,0.5,lyric="音"),N(2,0.5),N(1,0.5,lyric="叠",techniques=T_di()),N(6,0.5,octave=-1,lyric="音"),N(5,0.5),N(6,0.5,techniques=T_di()),N(1,0.5,octave=1)]},
    {"notes":[N(3,0.5,lyric="上",techniques=T_hu("up")),N(5,0.5,lyric="叠",techniques=T_di()),N(6,0.5,lyric="下",techniques=T_hu("down")),N(3,0.5,lyric="滑"),N(2,0.5),N(1,1,lyric="止"),D(0.5)]},
]))
all_scores.append(mk_score("打音与吐音", [
    {"notes":[N(5,0.5,lyric="打",techniques=T_da()),N(3,0.5,lyric="音"),N(2,0.5),N(1,0.5,lyric="打",techniques=T_da()),N(6,0.5,octave=-1,lyric="音"),N(5,0.5),N(3,0.5,techniques=T_da()),N(2,0.5,lyric="打")]},
    {"notes":[N(1,0.5,lyric="吐",techniques=T_tu()),N(2,0.5,lyric="音"),N(3,0.5),N(5,0.5,lyric="吐",techniques=T_tu()),N(6,0.5,lyric="音"),N(5,0.5),N(6,0.5,techniques=T_tu()),N(1,0.5,octave=1)]},
    {"notes":[N(3,0.5,lyric="打",techniques=T_da()),N(5,0.5,lyric="吐",techniques=T_tu()),N(6,0.5,lyric="打",techniques=T_da()),N(3,0.5,lyric="吐",techniques=T_tu()),N(5,0.5),N(6,0.5),N(3,0.5),N(2,0.5)]},
    {"notes":[N(1,1,lyric="打",techniques=T_da()),N(5,0.5,techniques=T_tu()),N(3,0.5,lyric="吐"),N(2,1,lyric="打",techniques=T_da()),N(1,1)]},
]))
all_scores.append(mk_score("连音与圆滑线", [
    {"notes":[N(5,0.5,lyric="圆",slurId="a1"),N(3,0.5,lyric="滑",slurId="a1"),N(2,0.5,lyric="圆",slurId="a2"),N(1,0.5,lyric="滑",slurId="a2"),N(6,0.5,octave=-1,lyric="圆",slurId="a3"),N(1,0.5,lyric="滑",slurId="a3"),N(2,0.5),N(3,0.5)]},
    {"notes":[N(5,1,lyric="连",tieId="t1"),N(5,0.5,tieId="t1"),N(5,0.5,lyric="音"),N(3,1,lyric="连",tieId="t2"),N(3,0.5,tieId="t2"),N(3,0.5,lyric="音")]},
    {"notes":[N(1,0.5,octave=1,lyric="月",slurId="a4"),N(6,0.5,lyric="亮",slurId="a4"),N(5,0.5,lyric="代",slurId="a5"),N(3,0.5,lyric="表",slurId="a5"),N(5,0.5,lyric="我",slurId="a6"),N(3,0.5,lyric="的",slurId="a6"),N(2,0.5,lyric="心"),N(1,0.5)]},
    {"notes":[N(5,1,lyric="跨",tieId="t3"),N(5,0.5,tieId="t3"),N(3,0.5,lyric="节"),N(2,1,lyric="大",slurId="a7"),N(1,1,lyric="圆",slurId="a7")]},
]))
all_scores.append(mk_score("反复跳跃", [
    {"notes":[N(5,0.5,lyric="前"),N(3,0.5,lyric="奏"),N(2,0.5,lyric="段"),N(1,0.5,lyric="落"),N(5,0.5,lyric="~"),N(3,0.5,lyric="~"),N(2,0.5,lyric="~"),N(1,0.5,lyric="~")]},
    {"notes":[N(6,0.5,octave=-1,lyric="主"),N(1,0.5,lyric="题"),N(2,0.5,lyric="乐"),N(3,0.5,lyric="段"),N(5,0.5,lyric="~"),N(6,0.5,lyric="~"),N(5,0.5,lyric="~"),N(3,0.5,lyric="~")]},
    {"notes":[N(1,1,lyric="反"),N(2,0.5,lyric="复"),N(3,0.5,lyric="开"),N(5,0.5,lyric="始"),N(6,0.5,lyric="~"),N(5,0.5,lyric="~"),N(3,0.5,lyric="~"),N(2,0.5,lyric="~")],"barline":"repeat-start"},
    {"notes":[N(1,1,lyric="一"),N(5,0.5,lyric="房"),N(3,0.5,lyric="结"),N(2,1,lyric="尾"),N(1,0.5,lyric="~")],"repeatEnding":{"numbers":[1]},"barline":"double"},
    {"notes":[N(5,0.5,lyric="间"),N(3,0.5,lyric="奏"),N(2,0.5,lyric="过"),N(1,0.5,lyric="渡"),N(6,0.5,octave=-1,lyric="~"),N(5,0.5,lyric="~"),N(6,0.25,octave=-1),N(1,0.25,lyric="~"),N(2,0.5,lyric="~")]},
    {"notes":[N(1,1,lyric="二"),N(5,0.5,lyric="房"),N(3,0.5,lyric="终"),N(2,1,lyric="止"),N(1,1)],"repeatEnding":{"numbers":[2]},"barline":"end"},
]))
all_scores.append(mk_score("力度与变化", [
    {"notes":[N(1,0.5,lyric="渐",dynamic="pp"),N(2,0.5,lyric="强"),N(3,0.5,lyric="自",dynamic="mp"),N(5,0.5,lyric="弱"),N(6,0.5,lyric="至"),N(1,0.5,octave=1,lyric="强",dynamic="f"),N(6,0.5),N(5,0.5)],"dynamics":{"type":"crescendo","endMeasureIndex":1}},
    {"notes":[N(1,0.25,octave=1,lyric="渐"),N(6,0.25,lyric="强"),N(5,0.25,lyric="至"),N(3,0.25,lyric="顶"),N(2,0.5,lyric="峰"),N(3,0.5),N(5,0.5),N(6,0.25),N(5,0.25)]},
    {"notes":[N(6,0.5,lyric="渐"),N(5,0.5,lyric="弱"),N(3,0.5,lyric="自"),N(2,0.5,lyric="强"),N(1,0.5,lyric="至"),N(6,0.5,octave=-1,lyric="弱"),N(5,0.5),N(3,0.5)],"dynamics":{"type":"descrescendo","endMeasureIndex":3}},
    {"notes":[N(2,0.5,lyric="渐"),N(1,0.5,lyric="弱"),N(6,0.5,octave=-1,lyric="至"),N(5,0.5,octave=-1,lyric="底"),N(6,0.25,octave=-1),N(1,0.25),N(2,0.5),N(3,0.5),N(1,0.5)]},
]))
all_scores.append(mk_score("综合符号示例", [
    {"notes":[N(5,0.5,lyric="综"),N(3,0.25,lyric="合"),N(2,0.25),N(1,0.5,lyric="符",techniques=T_bo()),N(6,0.5,octave=-1,lyric="号"),N(1,0.5,lyric="大"),N(2,0.5,lyric="全")]},
    {"notes":[N(3,0.5,lyric="顿",techniques=T_du()),N(5,0.25,lyric="滑",techniques=T_hu("up")),N(6,0.25,lyric="音"),N(3,0.5,lyric="波",techniques=T_bo()),N(2,0.5,lyric="保",tenuto=True),N(1,0.5,lyric="延",fermata=True),N(5,0.25,accidental="sharp",techniques=T_da()),N(3,0.25),N(2,0.5)]},
    {"notes":[N(6,0.5,lyric="打",techniques=T_da()),N(1,0.5,octave=1,lyric="叠",techniques=T_di()),N(5,0.5,lyric="吐",techniques=T_tu()),N(3,0.5,lyric="倚",techniques=T_yi(2)),N(5,0.5,lyric="颤",techniques=T_ch()),N(6,0.5,lyric="顿",techniques=T_du()),N(5,0.5)]},
    {"notes":[N(1,1,octave=1,lyric="低",slurId="z1"),N(6,0.5,lyric="音",slurId="z1"),N(5,1,lyric="连",tieId="zt1"),N(5,0.5,tieId="zt1"),N(3,0.5),N(2,0.25),N(1,0.25)]},
    {"notes":[N(2,0.5,lyric="跨",slurId="z2"),N(3,0.5,lyric="节",slurId="z2"),N(5,1,lyric="长",fermata=True),N(6,0.5,octave=-1,techniques=T_du()),N(1,0.5,lyric="止"),N(2,1)],"barline":"end"},
]))

# 参数组合池 (确保多样性)
param_sets = [
    {},                                                                 # 纯旋律
    {"use_oct": True}, {"use_acc": True}, {"use_rest": True},
    {"use_ten": True, "use_fer": True}, {"use_dyn": True},
    {"use_tech": True}, {"use_tech": True}, {"use_tech": True},
    {"use_slur": True}, {"use_tie": True},
    {"use_dunyin": True},
    {"use_slur": True, "use_tie": True},
    {"use_tech": True, "use_dyn": True},
    {"use_tech": True, "use_oct": True},
    {"use_tech": True, "use_slur": True},
    {"use_tech": True, "use_dunyin": True},
    {"use_slur": True, "use_oct": True},
    {"use_acc": True, "use_tie": True},
    {"use_rest": True, "use_dyn": True},
    {"use_tech": True, "use_slur": True, "use_dyn": True},
    {"use_tech": True, "use_oct": True, "use_tie": True},
    {"use_tech": True, "use_dyn": True, "use_rest": True},
    {"use_slur": True, "use_tie": True, "use_oct": True, "use_acc": True},
    {"use_tech": True, "use_slur": True, "use_dyn": True, "use_oct": True},
    {"use_tech": True, "use_slur": True, "use_tie": True, "use_dyn": True, "use_oct": True, "use_acc": True, "use_rest": True, "use_dunyin": True},
]

n_measures_pool = [2,3,3,4,4,4,4,5,5,6]

for i in range(2000 - 9):
    params = random.choice(param_sets)
    n_m = random.choice(n_measures_pool)
    measures = mk_measures(n_m, **params)
    all_scores.append(mk_score(f"素材{i+10:04d}", measures))

os.makedirs("public/training", exist_ok=True)
for i, s in enumerate(all_scores):
    fname = f"public/training/score_{i+1:04d}.json"
    with open(fname, "w") as f:
        json.dump(s, f, ensure_ascii=False, indent=2)
    beats = sum(n.get("duration",0)*(1.5 if n.get("dot") else 1) for m in s["measures"] for n in m["notes"])
    print(f"✓ {fname} ({len(s['measures'])}小节, {beats:.1f}拍)")

scores_list = [{"file": f"score_{i+1:04d}.json", "title": s["title"], "measures": len(s["measures"])} for i,s in enumerate(all_scores)]
with open("public/training/index.json", "w") as f:
    json.dump(scores_list, f, ensure_ascii=False, indent=2)
print(f"\nDone! {len(all_scores)} scores → public/training/")
