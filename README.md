# mars-y

`mars-y` 是 `mars-y.com` 的站点仓库。这个目录只负责站点内容、博客、子工具和 Cloudflare Pages 发布流程。

## 目录结构

```txt
mars-y/
├─ index.html
├─ assets/
├─ blog/
│  ├─ index.html
│  ├─ assets/
│  └─ posts/
├─ tools/
│  └─ json-to-cpaorsub-offline/
├─ .agents/
│  └─ skills/
│     └─ mars-y-pages-release/
└─ README.md
```

## 内容分类

- `index.html`：站点首页，提供工具和博客入口。
- `assets/`：站点级 favicon、logo、公开图片资源。
- `blog/`：博客子站，发布后访问 `/blog/`。
- `blog/posts/`：每日博客文章，每篇文章一个独立目录。
- `tools/json-to-cpaorsub-offline/`：原 JSON / CPA / SUB 离线转换器子工具。
- `.agents/skills/mars-y-pages-release/`：站点级发布技能，按 Codex skill 官方结构维护。

## 访问路径

```txt
https://mars-y.com/
https://mars-y.com/blog/
https://mars-y.com/tools/json-to-cpaorsub-offline/
```

## 博客使用

当前第一篇正式博客：

```txt
blog/posts/2026-06-03-ai-three-years-nine-lessons/index.html
```

保留的流程测试文章：

```txt
blog/posts/2026-06-03-daily-ai-content-workflow/index.html
```

后续每天新增文章时，建议使用：

```txt
blog/posts/yyyy-mm-dd-title/index.html
```

如果后续加入 Markdown 自动生成流程，建议把草稿和来源放到：

```txt
blog/content/
```

## 博客模板

后续博客优先使用 HTML Anything 的 Ofox Clay 文章模板：

```txt
E:\ai\product\html-anything\next\src\lib\templates\skills\article-ofox-clay-editorial\SKILL.md
E:\ai\product\html-anything\next\src\lib\templates\skills\article-ofox-clay-editorial\example.html
```

使用方式：

1. 将抓取结果、Markdown 草稿或原始素材准备好。
2. 参考 `SKILL.md` 的视觉和结构约束，使用 `example.html` 作为 HTML 结构参考。
3. 输出单文件 HTML，放入 `blog/posts/yyyy-mm-dd-title/index.html`。
4. 如果文章引用本地图片，把图片目录放在同一文章目录下，例如 `images/`。
5. 更新 `blog/index.html` 的 featured card 和文章列表。
6. 运行静态路径检查后提交并推送。

本次首篇博客来源产物：

```txt
E:\ai\product\catchit\artifacts\wechat-vTv0Vu4RgrMkmLbXGvnSug
```

已发布到站点目录：

```txt
blog/posts/2026-06-03-ai-three-years-nine-lessons/
```

## 子工具

转换器说明见：

```txt
tools/json-to-cpaorsub-offline/README.md
```

命令行工具示例：

```powershell
cd E:\ai\cloudflare\mars-y\tools\json-to-cpaorsub-offline
python .\card_to_cpa_sub.py .\input.txt
python .\cpa_to_card_sub.py .\cpa.tar
python .\split_lines.py
```

## 发布到 Cloudflare Pages

站点级 skill：

```txt
.agents/skills/mars-y-pages-release/SKILL.md
```

如果 Cloudflare Pages 已连接 GitHub，提交并推送即可发布：

```powershell
cd E:\ai\cloudflare\mars-y
git status --short --branch
git add index.html assets blog tools README.md .agents
git commit -m "organize mars-y site"
git push origin main
```

如果需要手动部署，按 `.agents/skills/mars-y-pages-release/SKILL.md` 的 Pages deploy 流程执行。

## 安全规则

不要提交或发布：

- `.env`
- GitHub token、Cloudflare token
- OAuth access token、refresh token、id token
- 邮箱、密码、API Key
- 真实卡密文件
- CPA / SUB 输出文件
- 生成出来的 `.tar`、`.zip`、`.json`、`.txt` 数据文件
- `.wrangler/`
- `.deploy-*`
