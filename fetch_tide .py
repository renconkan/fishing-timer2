#!/usr/bin/env python3
"""
tide736.net から武庫川一文字・南港・淡路島の
潮汐データを取得して tide_data.json に保存するスクリプト。
GitHub Actions から毎日 JST 0:00 に実行される。
"""

import urllib.request
import json
import datetime

# JST = UTC+9
jst = datetime.timezone(datetime.timedelta(hours=9))
today = datetime.datetime.now(jst)

LOCATIONS = {
    "mukogawa": {"pc": 28, "hc": 6,  "name": "武庫川一文字"},
    "nanko":    {"pc": 27, "hc": 1,  "name": "南港魚つり園"},
    "awaji":    {"pc": 28, "hc": 4,  "name": "淡路島"},
}

result = {
    "generated": today.strftime("%Y-%m-%d %H:%M JST"),
    "date": today.strftime("%Y-%m-%d"),
    "locations": {}
}

for key, loc in LOCATIONS.items():
    url = (
        f"https://api.tide736.net/get_tide.php"
        f"?pc={loc['pc']}&hc={loc['hc']}"
        f"&yr={today.year}&mn={today.month}&dy={today.day}"
        f"&rg=day"
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as res:
            data = json.loads(res.read().decode("utf-8"))

        date_key = today.strftime("%Y-%m-%d")
        chart = data["tide"]["chart"][date_key]
        raw = chart["tide"]   # 10分刻み 144点

        # 10分刻みのデータ → 時刻(分)とcmのペアリスト（全144点=24時間）
        tide_minutes = []
        for i, entry in enumerate(raw):
            if entry and i * 10 < 1440:  # 1440分=24時間
                tide_minutes.append({
                    "min": i * 10,
                    "cm": int(entry["cm"])
                })

        # 満潮・干潮
        floods = [{"time": f["time"], "cm": int(f["cm"])} for f in chart.get("flood", [])]
        edds   = [{"time": e["time"], "cm": int(e["cm"])} for e in chart.get("edd",   [])]

        result["locations"][key] = {
            "name": loc["name"],
            "tide_minutes": tide_minutes,
            "flood": floods,
            "ebb":   edds,
            "moon":  chart.get("moon", {}).get("title", ""),
        }
        print(f"✅ {loc['name']} 取得成功 (満潮{len(floods)}回, 干潮{len(edds)}回)")

    except Exception as e:
        print(f"❌ {loc['name']} 取得失敗: {e}")
        result["locations"][key] = {"name": loc["name"], "error": str(e)}

with open("tide_data.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f"\n✅ tide_data.json を保存しました ({today.strftime('%Y-%m-%d')})")
