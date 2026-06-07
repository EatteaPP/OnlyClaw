# open-url Skill

## Capability

Open a URL with the default browser or a specified browser.

## Supported browsers

- `default`
- `edge`
- `chrome`
- `firefox`

## When to use

Use this skill when the user asks to open a URL, link, or website.

Examples:

- open https://www.google.com
- open edge https://github.com
- open chrome https://www.google.com
- open firefox https://www.mozilla.org

## Parameters

```json
{
  "url": "https://www.google.com",
  "browser": "default | edge | chrome | firefox"
}
```

## URL Policy

Allowed URL schemes:

- `http`
- `https`

Forbidden URL schemes:

- `javascript`
- `file`
- `data`
- `powershell`
- `cmd`
- any unsupported or unknown scheme

## Policy

This skill may only open a URL.

This skill must not:

- click web pages
- submit forms
- log into websites
- scrape web pages
- read browser contents
- automate browser behavior after launch
- execute arbitrary shell commands

