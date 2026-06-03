---
name: mars-y-pages-release
description: Deploy, publish, update, and verify the mars-y.com Cloudflare Pages static site. Use when working on mars-y site content, blog pages, child tools under tools/, DNS handoff, GitHub push, or Cloudflare Pages release tasks.
---

# Mars-y Pages Release

Use this skill for `mars-y.com` site maintenance and release work.

## Project Facts

- Site root: `E:\ai\cloudflare\mars-y`
- GitHub remote: `https://github.com/liaosong0187765-maker/json-to-cpaorsub-offline`
- Cloudflare Pages project: `mars-y`
- Pages URL: `https://mars-y.pages.dev`
- Custom domain: `https://mars-y.com`
- Site home: `index.html`
- Blog home: `blog/index.html`
- Child tool: `tools/json-to-cpaorsub-offline/index.html`
- Site assets: `assets/`

## Structure Rules

- Keep site-level content at root: `index.html`, `assets/`, `blog/`, `tools/`, `README.md`.
- Keep daily blog content under `blog/posts/yyyy-mm-dd-title/index.html`.
- Keep converter files under `tools/json-to-cpaorsub-offline/`.
- Keep repo skills under `.agents/skills/<skill-name>/SKILL.md`.
- Do not put auxiliary `README.md` files inside skill folders.

## Startup

```powershell
cd E:\ai\cloudflare\mars-y
Get-ChildItem -Force
git status --short --branch
git diff --stat
git remote -v
```

Check key static references:

```powershell
rg -n "(src=|href=|assets/|blog/|tools/|README)" index.html blog tools
```

## Deploy To Cloudflare Pages

Create a clean publish directory containing only public site files:

```powershell
$root = 'E:\ai\cloudflare\mars-y'
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$publish = Join-Path $root ".deploy-mars-y-$stamp"
New-Item -ItemType Directory -Path $publish | Out-Null

Copy-Item -LiteralPath "$root\index.html" -Destination (Join-Path $publish 'index.html')
Copy-Item -LiteralPath "$root\README.md" -Destination (Join-Path $publish 'README.md')
Copy-Item -LiteralPath "$root\assets" -Destination (Join-Path $publish 'assets') -Recurse
Copy-Item -LiteralPath "$root\blog" -Destination (Join-Path $publish 'blog') -Recurse
Copy-Item -LiteralPath "$root\tools" -Destination (Join-Path $publish 'tools') -Recurse
Write-Output $publish
```

Deploy:

```powershell
& 'C:\Users\111\AppData\Local\Volta\tools\image\node\22.22.2\node.exe' `
  'E:\ai\product\cloudflare_temp_email\pages\node_modules\wrangler\bin\wrangler.js' `
  pages deploy $publish --project-name=mars-y --branch=main `
  --commit-message='Deploy mars-y static site'
```

Verify:

```powershell
@'
(async () => {
  for (const url of [
    'https://mars-y.pages.dev',
    'https://mars-y.pages.dev/blog/',
    'https://mars-y.pages.dev/tools/json-to-cpaorsub-offline/',
    'https://mars-y.com',
    'https://mars-y.com/blog/',
    'https://mars-y.com/tools/json-to-cpaorsub-offline/'
  ]) {
    try {
      const res = await fetch(url, { redirect: 'follow' });
      const text = await res.text();
      const title = text.match(/<title>(.*?)<\/title>/i)?.[1] || '';
      console.log(JSON.stringify({ url, status: res.status, ok: res.ok, title, length: text.length }));
    } catch (err) {
      console.log(JSON.stringify({ url, error: err.message }));
    }
  }
})();
'@ | & 'C:\Users\111\AppData\Local\Volta\tools\image\node\22.22.2\node.exe'
```

## GitHub Update Flow

Before push:

```powershell
git status --short --branch
git diff --stat
git diff
```

Stage only intended site files:

```powershell
git add index.html assets blog tools README.md .agents
git commit -m "update mars-y site"
git push origin main
```

If GitHub auth fails, refresh locally:

```powershell
gh auth login -h github.com --web
```

Do not paste or store tokens.

## DNS Handoff

If `mars-y.com` returns `522` or Pages says `CNAME record not set`, Cloudflare DNS is still pointing at an old origin.

Use Cloudflare Dashboard:

1. Open `mars-y.com` -> `DNS` -> `Records`.
2. Delete old apex `A` records such as `@ -> 198.18.0.182`.
3. Add `CNAME @ -> mars-y.pages.dev`, proxied, TTL Auto.
4. Optional: add `CNAME www -> mars-y.pages.dev`, proxied, TTL Auto.

Chrome automation may be blocked from `dash.cloudflare.com`; if blocked, give the user manual steps and do not bypass.

## Safety

Never commit or publish:

- `.env`
- Cloudflare or GitHub tokens
- OAuth tokens
- real card/account files
- generated CPA/SUB outputs
- `.wrangler/`
- `.deploy-*`
