#!/usr/bin/env python3
"""
生成活动映射文件 (event_map.json)

复用 Next.js 前端 /events/ 路由中的筛选逻辑：
  - buildEventRawUnitMap: 从 actionSets.json 解析 eventId → 活动团体
  - buildEventBannerCharMap: 从 eventStories.json + gameCharacterUnits.json 解析 eventId → 封面角色

分类规则：
  - world_bloom (世界绽放) → "wl活" (worldlink)
  - 有活动团体且非 mixed → "箱活"，按封面角色分类，如 "ick一箱", "ick二箱"
  - 无活动团体或 mixed → "混活"

输出格式 (event_map.json):
{
  "events": {
    "1": {
      "id": 1,
      "name": "雨上がりの一番星",
      "eventType": "marathon",
      "category": "箱活",
      "eventUnit": "ln",
      "bannerCharId": 2,
      "bannerCharNick": "saki",
      "boxLabel": "saki一箱"
    },
    ...
  },
  "meta": {
    "generatedAt": "...",
    "totalEvents": 202,
    "boxEvents": 170,
    "mixedEvents": 18,
    "wlEvents": 14
  }
}
"""

import json
import urllib.request
import gzip
import sys
import os
from datetime import datetime
from collections import defaultdict

# ---------------------------------------------------------------------------
# 配置
# ---------------------------------------------------------------------------

MASTER_BASE_URL = "https://sekaimaster.exmeaning.com/master"
FALLBACK_BASE_URL = "https://sk.exmeaning.com/master"

# 活动团体映射 (复用自 EventFilters.tsx EVENT_TYPE_TO_FILTER_ID)
EVENT_TYPE_TO_FILTER_ID = {
    "band": "ln",
    "idol": "mmj",
    "street": "vbs",
    "wonder": "ws",
    "night": "25ji",
    "piapro": "vs",
}

# 中文数字映射 (用于箱活编号)
CN_NUM = ["零", "一", "二", "三", "四", "五", "六", "七", "八", "九", "十",
          "十一", "十二", "十三", "十四", "十五"]

# ---------------------------------------------------------------------------
# 数据获取
# ---------------------------------------------------------------------------

def fetch_json(path: str) -> list | dict:
    """从 masterdata 服务器获取 JSON 数据，支持 gzip 和 fallback"""
    for base_url in [MASTER_BASE_URL, FALLBACK_BASE_URL]:
        url = f"{base_url}/{path}"
        try:
            req = urllib.request.Request(url)
            req.add_header("Accept-Encoding", "gzip")
            with urllib.request.urlopen(req, timeout=120) as resp:
                raw = resp.read()
                if raw[:2] == b"\x1f\x8b":
                    raw = gzip.decompress(raw)
                return json.loads(raw)
        except Exception as e:
            print(f"  [WARN] Failed to fetch from {url}: {e}", file=sys.stderr)
    raise RuntimeError(f"Failed to fetch {path} from both primary and fallback servers")


def load_character_nicknames(yaml_path: str) -> dict[int, str]:
    """
    从 character_nicknames.yaml 读取角色 ID → 英文简称映射
    取每个角色 nicknames 列表的第一个元素作为英文简称
    """
    import re

    nicknames = {}
    with open(yaml_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 简单解析 YAML (无需引入 pyyaml 依赖)
    current_id = None
    current_nicknames = []
    in_nicknames_list = False

    for line in content.split("\n"):
        # 匹配 id 字段
        id_match = re.match(r"\s+-\s+id:\s+(\d+)", line)
        if id_match:
            if current_id is not None and current_nicknames:
                nicknames[current_id] = current_nicknames[0]
            current_id = int(id_match.group(1))
            current_nicknames = []
            in_nicknames_list = False
            continue

        # 匹配 nicknames 列表头
        if current_id is not None and re.match(r"\s+nicknames:\s*$", line):
            in_nicknames_list = True
            continue

        # 匹配昵称项
        if in_nicknames_list and current_id is not None:
            nick_match = re.match(r"\s+-\s+(.+)", line)
            if nick_match:
                current_nicknames.append(nick_match.group(1).strip())
            elif not re.match(r"\s*$", line):
                # 非空行且不是昵称项，说明 nicknames 列表结束
                in_nicknames_list = False

    # 处理最后一个
    if current_id is not None and current_nicknames:
        nicknames[current_id] = current_nicknames[0]

    return nicknames


# ---------------------------------------------------------------------------
# 核心逻辑 (复用自 eventUnit.ts)
# ---------------------------------------------------------------------------

def build_event_raw_unit_map(action_sets: list[dict]) -> dict[int, str]:
    """
    复用自 eventUnit.ts buildEventRawUnitMap()
    从 actionSets 数据构建 eventId → raw unit string 映射
    """
    raw_map: dict[int, str] = {1: "band", 5: "idol", 6: "street", 9: "shuffle"}

    for action in action_sets:
        rc_id = str(action.get("releaseConditionId", ""))
        scenario_id = action.get("scenarioId", "")

        if (
            scenario_id
            and ("areatalk_ev" in scenario_id or "areatalk_wl" in scenario_id)
            and len(rc_id) == 6
            and rc_id[0] == "1"
        ):
            event_id = int(rc_id[1:4]) + 1
            event_type = scenario_id.split("_")[2]
            if event_id not in raw_map:
                raw_map[event_id] = event_type

    return raw_map


def raw_unit_to_filter_id(raw: str) -> str:
    """
    复用自 eventUnit.ts rawUnitToFilterId()
    将 raw unit string 转换为 filter ID，未知类型返回 "mixed"
    """
    return EVENT_TYPE_TO_FILTER_ID.get(raw, "mixed")


def build_event_banner_char_map(
    event_stories: list[dict], chara_units: list[dict]
) -> dict[int, int]:
    """
    复用自 eventUnit.ts buildEventBannerCharMap()
    从 eventStories + gameCharacterUnits 构建 eventId → gameCharacterId 映射
    """
    unit_id_to_char_id = {cu["id"]: cu["gameCharacterId"] for cu in chara_units}

    banner_map: dict[int, int] = {}
    for story in event_stories:
        event_id = story["eventId"]
        # 特殊处理: Event 97 固定返回角色 ID 10
        if event_id == 97:
            banner_map[97] = 10
            continue

        banner_unit_id = story.get("bannerGameCharacterUnitId")
        if banner_unit_id is not None:
            char_id = unit_id_to_char_id.get(banner_unit_id)
            if char_id is not None:
                banner_map[event_id] = char_id

    return banner_map


# ---------------------------------------------------------------------------
# 分类逻辑
# ---------------------------------------------------------------------------

def load_existing_event_map(output_path: str) -> dict[int, str]:
    """
    加载已存在的 event_map.csv，返回 {event_id: boxLabel} 映射
    用于保留已手动设置的 boxLabel
    """
    if not os.path.exists(output_path):
        return {}
    try:
        import csv
        existing = {}
        with open(output_path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                event_id = int(row["id"])
                box_label = row.get("boxLabel", "")
                if box_label:
                    existing[event_id] = box_label
        return existing
    except Exception:
        return {}


def classify_events(
    events: list[dict],
    event_unit_map: dict[int, str],
    event_banner_char_map: dict[int, int],
    char_nicknames: dict[int, str],
    existing_events: dict[int, str],
) -> tuple[list[dict], dict]:
    """
    对所有活动进行分类，生成映射数据

    分类规则:
      - world_bloom → "wl活"
      - 有活动团体且非 mixed → "箱活"
      - 无活动团体或 mixed → "混活"

    箱活按封面角色编号: 如 ick一箱, ick二箱
    """
    # 先统计每个角色在箱活中出现的次数 (按 eventId 排序确定编号)
    box_events_by_char: dict[int, list[int]] = defaultdict(list)

    # 按 id 排序确保编号稳定
    sorted_events = sorted(events, key=lambda e: e["id"])

    for e in sorted_events:
        event_id = e["id"]
        event_type = e["eventType"]
        unit = event_unit_map.get(event_id)

        if event_type == "world_bloom":
            continue
        if unit and unit != "mixed":
            banner_char = event_banner_char_map.get(event_id)
            if banner_char:
                box_events_by_char[banner_char].append(event_id)

    # 为每个角色的箱活建立编号映射: eventId → 第几箱
    box_number_map: dict[int, dict[int, int]] = {}  # charId → {eventId → boxNumber}
    for char_id, event_ids in box_events_by_char.items():
        box_number_map[char_id] = {}
        for idx, eid in enumerate(event_ids, start=1):
            box_number_map[char_id][eid] = idx

    # 生成结果
    result_events: list[dict] = []
    stats = {"boxEvents": 0, "mixedEvents": 0, "wlEvents": 0}

    for e in sorted_events:
        event_id = e["id"]
        event_type = e["eventType"]
        unit = event_unit_map.get(event_id)
        banner_char = event_banner_char_map.get(event_id)

        # 计算分类和 boxLabel
        if event_type == "world_bloom":
            box_label = ""
            stats["wlEvents"] += 1
        elif unit and unit != "mixed":
            nick = char_nicknames.get(banner_char, f"char{banner_char}")
            box_num = box_number_map.get(banner_char, {}).get(event_id, 0)
            if 0 < box_num <= len(CN_NUM):
                box_label = f"{nick}{CN_NUM[box_num]}箱"
            else:
                box_label = f"{nick}{box_num}箱"
            stats["boxEvents"] += 1
        else:
            nick = char_nicknames.get(banner_char) if banner_char else ""
            # 混活: boxLabel 使用角色昵称作为别名
            # 若原文件中已有非空 boxLabel，则保留
            existing_box_label = existing_events.get(event_id)
            if existing_box_label:
                box_label = existing_box_label
            else:
                box_label = nick  # 使用角色昵称作为别名
            stats["mixedEvents"] += 1

        # 仅保留 id, name, boxLabel
        result_events.append({
            "id": event_id,
            "name": e["name"],
            "boxLabel": box_label,
        })

    return result_events, stats


# ---------------------------------------------------------------------------
# 主函数
# ---------------------------------------------------------------------------

def main():
    # 确定项目根目录 (脚本所在目录即为项目根目录)
    project_root = os.path.dirname(os.path.abspath(__file__))
    yaml_path = os.path.join(project_root, "character_nicknames.yaml")
    output_path = os.path.join(project_root, "story", "event", "event_map.csv")

    print("=" * 60)
    print("生成活动映射文件 (event_map.json)")
    print("=" * 60)

    # 1. 加载角色昵称
    print("\n[1/4] 加载角色昵称映射...")
    char_nicknames = load_character_nicknames(yaml_path)
    print(f"  已加载 {len(char_nicknames)} 个角色昵称")
    for cid in sorted(char_nicknames.keys())[:5]:
        print(f"    id={cid}: {char_nicknames[cid]}")
    print("    ...")

    # 2. 获取 masterdata
    print("\n[2/4] 从 masterdata 服务器获取数据...")
    print("  获取 events.json...")
    events = fetch_json("events.json")
    print(f"  共 {len(events)} 个活动")

    print("  获取 actionSets.json (JP)...")
    action_sets = fetch_json("actionSets.json")
    print(f"  共 {len(action_sets)} 条 actionSet")

    print("  获取 eventStories.json...")
    event_stories = fetch_json("eventStories.json")
    print(f"  共 {len(event_stories)} 条 eventStory")

    print("  获取 gameCharacterUnits.json...")
    chara_units = fetch_json("gameCharacterUnits.json")
    print(f"  共 {len(chara_units)} 个角色单位")

    # 3. 构建映射 (复用前端逻辑)
    print("\n[3/4] 构建活动映射 (复用前端筛选逻辑)...")

    # buildEventRawUnitMap
    raw_unit_map = build_event_raw_unit_map(action_sets)
    event_unit_map = {eid: raw_unit_to_filter_id(raw) for eid, raw in raw_unit_map.items()}
    print(f"  eventUnitMap: {len(event_unit_map)} 条映射")

    # buildEventBannerCharMap
    event_banner_char_map = build_event_banner_char_map(event_stories, chara_units)
    print(f"  eventBannerCharMap: {len(event_banner_char_map)} 条映射")

    # 4. 分类并生成输出
    print("\n[4/4] 分类活动并生成映射文件...")
    # 加载已存在的 event_map.csv，用于保留手动设置的 boxLabel
    existing_events = load_existing_event_map(output_path)
    if existing_events:
        print(f"  已加载现有 event_map.csv，共 {len(existing_events)} 条记录")
    result_events, stats = classify_events(
        events, event_unit_map, event_banner_char_map, char_nicknames, existing_events
    )

    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # 写入 CSV 文件
    import csv
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "name", "boxLabel"])
        writer.writeheader()
        writer.writerows(result_events)

    print(f"\n  已写入: {output_path}")
    print(f"\n{'=' * 60}")
    print(f"统计:")
    print(f"  总活动数: {stats['boxEvents'] + stats['mixedEvents'] + stats['wlEvents']}")
    print(f"  箱活: {stats['boxEvents']}")
    print(f"  混活: {stats['mixedEvents']}")
    print(f"  wl活: {stats['wlEvents']}")
    print(f"{'=' * 60}")

    # 打印一些示例
    print("\n示例 (前10个活动):")
    for e in result_events[:10]:
        label = e["boxLabel"] or "(无)"
        print(f"  id={e['id']:3d} | {label:10s} | {e['name'][:25]}")


if __name__ == "__main__":
    main()
