# ProjectSekai 剧情资源仓库

Crawled by [ProjectSekai & BangDream story crawler](https://github.com/ci-ke/ProjectSekai-BangDream-story-crawler)

[Online reading](https://ci-ke.github.io/story)

本仓库存储《世界计划 多彩舞台！feat. 初音未来》(ProjectSekai / プロセカ) 的中文剧情文本资源，供 AI 检索与阅读使用。

---

## 仓库总览

```
ProjectSekai-story/
├── worldview.txt                  # 世界观设定
├── character_nicknames.yaml       # 角色别名表
├── story/
│   ├── unit/                      # 主线剧情
│   ├── event/                     # 活动剧情
│   ├── card/                      # 角色卡牌剧情
│   ├── area/                      # 区域对话
│   ├── self/                      # 角色个人介绍
│   └── special/                   # 番外/特殊剧情
└── migrate_story_paths.py         # 数据迁移脚本
```

---

## 根目录文件

| 文件 | 说明 |
|------|------|
| `worldview.txt` | 世界观设定，包含现实世界与「世界」的背景、各组合及其成员介绍 |
| `character_nicknames.yaml` | 角色别名映射表，`id` 对应角色 ID，`nicknames` 为该角色的各种称呼（缩写、日文名、中文名、粉丝昵称等） |

---

## story/unit — 主线剧情

按组合 ID 分目录，每个目录下为该组合主线各话的文本文件。

| 目录 ID | 组合名 | 文件数 | 文件命名规则 |
|---------|--------|--------|-------------|
| 1 | VIRTUAL SINGER (VS) | 20 | `vs{target}_01_{ep}.txt`，target 为 leo/mmj/street/nightcode/wonder |
| 2 | Leo/need (Ln) | 21 | `leo_{chapter}_{ep}.txt`，ep=00 为序章 |
| 3 | MORE MORE JUMP! (MMJ) | 21 | `mmj_{chapter}_{ep}.txt` |
| 4 | Vivid BAD SQUAD (VBS) | 21 | `vbs_{chapter}_{ep}.txt` |
| 5 | Wonderlands×Showtime (WxS) | 21 | `wonder_{chapter}_{ep}.txt` |
| 6 | 25-ji, Nightcord de. (25h/niigo) | 21 | `nightcode_{chapter}_{ep}.txt` |

- unit/1 (VS) 的文件名格式为 `vs{目标组合缩写}_01_{话数}.txt`，表示虚拟歌手在该组合「世界」中的主线剧情。
- unit/2~6 的文件名格式为 `{组合缩写}_{章}_{话}.txt`，其中话数 `00` 为序章，`01` 起为正篇。

---

## story/event — 活动剧情

每个活动一个目录，目录名为活动 ID（1~200+）。

```
story/event/{eventId}/
├── detail.json    # AI 生成的活动剧情总结
├── 1.txt          # 第1话
├── 2.txt          # 第2话
├── ...
└── 8.txt          # 第8话
```

### 活动别名查询

`story/event/event_map.csv` 提供活动 ID 与别名的映射，便于快速定位活动：

| 字段 | 说明 |
|------|------|
| `id` | 活动 ID（对应目录名） |
| `name` | 活动日文名 |
| `boxLabel` | 活动别名（如 `saki一箱`、`体育混` 等） |

**使用示例**：
- 查找「雨上がりの一番星」→ `boxLabel` 为 `saki一箱` → 对应 `id=1` → 访问 `story/event/1/`
- 别名命名规则：`{角色缩写}{箱数}` 表示该角色的第 N 箱活，`混` 表示混合活动，无后缀表示非箱活

### detail.json 结构

```json
{
  "event_id": 1,
  "title_jp": "雨上がりの一番星",
  "title_cn": "雨后初星",
  "outline_jp": "...",
  "outline_cn": "...",
  "summary_cn": "活动整体剧情摘要",
  "chapters": [
    {
      "chapter_no": 1,
      "title_jp": "...",
      "title_cn": "...",
      "summary_cn": "该话剧情摘要",
      "character_ids": [],
      "image_url": "..."
    }
  ]
}
```

- `detail.json` 为 AI 生成的结构化总结，包含活动标题（日/中）、大纲、整体摘要及每话摘要。
- `1.txt` ~ `8.txt` 为该活动各话的完整剧情文本。

---

## story/card — 角色卡牌剧情

每个卡牌一个文件，文件名为卡牌 ID。

```
story/card/{cardId}.txt
```

- 共约 1300 个卡牌剧情文件。
- 每个文件包含该卡牌的前篇和后篇剧情。
- 文件首行格式：`{cardId}_{角色名}_{稀有度标识} {卡牌标题}`。

---

## story/area — 区域对话

按类别分子目录，每个子目录下为该类别各区域对话的文本文件。

### 子目录分类

| 目录名 | 说明 | 数量 |
|--------|------|------|
| `event_{id}` | 活动 `id` 结束后新增的区域对话 | 197 个目录 |
| `grade1` | 一年级区域对话 | 1 |
| `grade2` | 二年级区域对话 | 1 |
| `aprilfool{year}` | 愚人节特别区域对话 (2022~2026) | 5 |
| `limited_{id}` | 限定区域对话 | 3 |
| `theater` | 剧场区域对话 | 1 |

### 文件结构

```
story/area/{category}/
├── _all.txt          # 该类别所有区域对话的合并文本
├── {actionSetId}.txt # 单条区域对话
└── ...
```

- 每个区域对话文件首行格式：`{unitId} {actionSetId} {type} 【{地点名}】`，其中 type 为 `area`（常驻）或 `event`（活动限定）。
- `_all.txt` 为该类别下所有区域对话的合并文件，便于批量检索。

---

## story/self — 角色个人介绍

每个角色一个文件，文件名为角色 ID。

```
story/self/{charaId}.txt
```

- 共 22 个文件，覆盖全部可玩角色及虚拟歌手。
- 每个文件按学年分段（`《YEAR 1》`、`《YEAR 2》`），包含该角色在不同时期的自我介绍剧情。

### 角色 ID 对照

| ID | 角色 | 组合 |
|----|------|------|
| 1 | 星乃一歌 | Leo/need |
| 2 | 天马咲希 | Leo/need |
| 3 | 望月穗波 | Leo/need |
| 4 | 日野森志步 | Leo/need |
| 5 | 花里实乃里 | MORE MORE JUMP! |
| 6 | 桐谷遥 | MORE MORE JUMP! |
| 7 | 桃井爱莉 | MORE MORE JUMP! |
| 8 | 日野森雫 | MORE MORE JUMP! |
| 9 | 小豆沢心羽 | Vivid BAD SQUAD |
| 10 | 白石杏 | Vivid BAD SQUAD |
| 11 | 东云彰人 | Vivid BAD SQUAD |
| 12 | 青柳冬弥 | Vivid BAD SQUAD |
| 13 | 天马司 | Wonderlands×Showtime |
| 14 | 凤笑梦 | Wonderlands×Showtime |
| 15 | 草薙宁宁 | Wonderlands×Showtime |
| 16 | 神代类 | Wonderlands×Showtime |
| 17 | 宵崎奏 | 25-ji, Nightcord de. |
| 18 | 朝比奈真冬 | 25-ji, Nightcord de. |
| 19 | 东云绘名 | 25-ji, Nightcord de. |
| 20 | 晓山瑞希 | 25-ji, Nightcord de. |
| 21 | 初音未来 | Virtual Singer |
| 22 | 镜音铃 | Virtual Singer |
| 23 | 镜音连 | Virtual Singer |
| 24 | 巡音流歌 | Virtual Singer |
| 25 | MEIKO | Virtual Singer |
| 26 | KAITO | Virtual Singer |

---

## story/special — 番外/特殊剧情

每个特殊剧情一个文件，文件名为特殊剧情 ID。

```
story/special/{spId}.txt
```

- 共 64 个文件。
- 内容包括：周年纪念动画、联动剧情、直播特别篇等。
- 文件首行格式：`sp{spId}_{标题标识}`。

---

## 剧情文本通用格式

所有剧情文本文件（.txt）遵循以下格式约定：

1. **首行**：剧情概要或标识信息
2. **第二段**：话数标识（如 `1-1 孤独的雨` 或 `leo_01_01 秘密练习`）
3. **登场角色**：`（登场角色：角色A、角色B、...）`
4. **正文**：以 `角色名：台词` 或 `（舞台指示）` 的格式书写

---

## AI 检索指引

### 按角色查找剧情

1. 通过 `character_nicknames.yaml` 确认角色 ID
2. 个人介绍：`story/self/{charaId}.txt`
3. 卡牌剧情：在 `story/card/` 中搜索文件首行包含角色名的文件
4. 主线剧情：根据角色所属组合，检索 `story/unit/{unitId}/` 下相关文件
5. 活动剧情：检索 `story/event/*/detail.json` 中 `character_ids` 包含该角色 ID 的活动

### 按活动查找剧情

1. 活动概要：`story/event/{eventId}/detail.json`（含标题、摘要、每话摘要）
2. 活动全文：`story/event/{eventId}/{1-8}.txt`
3. 活动区域对话：`story/area/event_{eventId}/`

### 按组合查找主线

| 组合 | unitId | 检索路径 |
|------|--------|----------|
| VIRTUAL SINGER | 1 | `story/unit/1/` |
| Leo/need | 2 | `story/unit/2/` |
| MORE MORE JUMP! | 3 | `story/unit/3/` |
| Vivid BAD SQUAD | 4 | `story/unit/4/` |
| Wonderlands×Showtime | 5 | `story/unit/5/` |
| 25-ji, Nightcord de. | 6 | `story/unit/6/` |
