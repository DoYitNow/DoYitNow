# Codex Skills

This directory contains portable Codex skills that can be copied into a local
`$CODEX_HOME/skills` or `~/.codex/skills` directory.

## Available Skills

- [`image-to-svg`](image-to-svg/) converts images into self-contained SVG files.
  It uses handcrafted semantic reconstruction for simple graphics and
  source-aligned posterized vectorization for photographs and portraits.

## Install A Skill

Copy a skill folder into your Codex skills directory:

```powershell
Copy-Item -Recurse -Force .\skills\image-to-svg "$env:USERPROFILE\.codex\skills\image-to-svg"
```

Restart Codex or reload skills after copying so the updated metadata is
discovered.
