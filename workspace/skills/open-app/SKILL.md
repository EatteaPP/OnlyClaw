# open-app Skill

## Capability

Open a local application from an allowlist.

## Supported apps

- `default_browser`
- `edge`
- `chrome`
- `firefox`
- `notepad`
- `calculator`

## Supported aliases

`open-app` only accepts aliases registered in `skill.yaml`.

Examples:

- `browser` -> `default_browser`
- `default browser` -> `default_browser`
- `edge` -> `edge`
- `msedge` -> `edge`
- `chrome` -> `chrome`
- `firefox` -> `firefox`
- `calc` -> `calculator`

## When to use

Use this skill when the user asks to open a local application.

Examples:

- open browser
- open edge
- open chrome
- open firefox
- open notepad
- open calculator
- open calc

## Parameters

```json
{
  "app": "default_browser | edge | chrome | firefox | notepad | calculator"
}
```

## Policy

This skill may only open allowlisted local applications.

This skill must not:

- execute arbitrary shell commands
- open unregistered applications
- pass arbitrary command-line arguments
- automate application behavior after launch
- click UI elements
- read application contents
- submit forms
