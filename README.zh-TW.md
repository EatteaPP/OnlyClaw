# OnlyClaw

OnlyClaw 是一個基於「No Skill, No Action」原則的 Windows 桌面命令面板。

## 核心原則

No Skill, No Action。

OnlyClaw 只會執行已註冊的 skill。  
如果沒有對應 skill，就必須回報能力不足。

## Skills

Skill 放在：

```text
workspace/skills/
```

每個 skill 應包含：

- `SKILL.md`
- `skill.yaml`
- `scripts/`
- `examples/`

本版本內建 skill：

- `open-app`
- `open-url`

## 執行流程

所有動作都必須經過：

`Skill Registry` -> `Executor` -> `Script` -> `Structured Result`

Executor 目前只支援 Python script，並且必須：

- 使用 `shell=False`
- 透過 JSON stdin 傳入參數
- 解析 JSON stdout
- 寫入執行 log

## 安全規則

OnlyClaw 不得：

- 執行任意 shell command
- 使用 `shell=True`
- 執行未註冊 skill
- 開啟不支援的 URL scheme
- 自動化瀏覽器後續操作
- 點擊 UI
- 提交表單
- 登入網站

