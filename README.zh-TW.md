# OnlyClaw

OnlyClaw 是一個 Windows 常駐型桌面指令工具，遵守 **No Skill, No Action** 原則。

如果沒有註冊過的 skill，OnlyClaw 就不應執行動作。

## 專案目標

OnlyClaw 不是通用型自主 AI Agent。

它的角色很單純：

- 顯示浮動指令視窗
- 監聽可設定的熱鍵
- 將指令對應到已註冊的 skill
- 透過 Executor 執行允許的本機 script
- 回傳結構化結果
- 寫入執行紀錄

## Current Built-in Skills

### open-app

開啟允許清單中的本機應用程式。

範例：

```text
open browser
open edge
open chrome
open notepad
open calculator
```

### open-url

開啟 HTTP 或 HTTPS 網址。

範例：

```text
open https://www.google.com
open edge https://github.com
```

## Window Behavior Configuration

視窗行為可在 `config.yaml` 中設定：

```yaml
behavior:
  hide_on_escape: true
  hide_on_lost_focus: true
  hide_on_hotkey_when_visible: true
  focus_textbox_on_show: true
  select_all_text_on_show: true
```

啟用後，OnlyClaw 會像暫時性的 command palette：

- 快速連按兩下 Ctrl 顯示視窗
- 視窗顯示時再快速連按兩下 Ctrl 會隱藏
- 按 Esc 會隱藏視窗
- 失去焦點會隱藏視窗

## Repository Status

這個專案目前是個個人 POC。

目前重點：

- Windows 桌面工具
- skill registry
- safe executor
- mock provider
- Gemini / OpenAI provider interface

尚未實作：

- production packaging
- installer
- voice input
- enterprise authentication
- advanced browser automation
