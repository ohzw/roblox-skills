# Roblox Skills

[![skills.sh](https://skills.sh/b/ohzw/roblox-skills)](https://skills.sh/ohzw/roblox-skills)

A collection of AI Agent Skills for Roblox development, designed for use with [skills.sh](https://skills.sh).

## Available Skills

| Skill | Description |
|---|---|
| [`roblox-open-cloud`](./skills/roblox-open-cloud) | Securely resolve and call Roblox Open Cloud REST APIs with API-key authentication. |

## Installation

Install all skills globally:

```bash
npx skills add ohzw/roblox-skills -g
```

Install a specific skill:

```bash
npx skills add ohzw/roblox-skills --skill roblox-open-cloud -g
```

## Local Development

```bash
git clone https://github.com/ohzw/roblox-skills.git
npx skills add ./roblox-skills -g
```

## Eval workspace (optional, for local continuity)

This repo stores eval artifacts under:
`skills/roblox-open-cloud/evals/workspace`.

If you already use legacy paths such as `~/.agents/skills/roblox-open-cloud-workspace`, recreate them as a symlink after cloning:

```bash
mkdir -p ~/.agents/skills
ln -s ~/Documents/Github/roblox-skills/skills/roblox-open-cloud/evals/workspace ~/.agents/skills/roblox-open-cloud-workspace
```

Remove existing directories first if they already exist:

```bash
rm -rf ~/.agents/skills/roblox-open-cloud-workspace
ln -s ~/Documents/Github/roblox-skills/skills/roblox-open-cloud/evals/workspace ~/.agents/skills/roblox-open-cloud-workspace
```

You can keep this link even after `npx skills add` installation to keep local scripts that expect the old location working.

## License

[MIT](./LICENSE)
