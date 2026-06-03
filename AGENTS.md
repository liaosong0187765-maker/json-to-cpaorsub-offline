# mars-y Agent Instructions

## Language

- 默认使用中文回复。
- 技术术语、命令、路径、API 字段名、文件名和代码标识符保留英文。
- 输出要简洁、结构清晰、可执行。

## Project Scope

`mars-y` 是 `mars-y.com` 的静态站点仓库，负责：

- 站点首页
- 博客入口和博客文章
- 独立子工具页面
- Cloudflare Pages 发布相关文件
- 本项目内可复用的 agent skills 和脚本

不要把无关项目、临时实验、原始抓取大文件或私密数据放进这个仓库。

## Startup Checklist

进入本项目后先读取：

1. `AGENTS.md`
2. `README.md`
3. `.gitignore`
4. `git status --short --branch`
5. `git diff`

如果发现已有未提交修改，先判断是否与当前任务相关。不要覆盖、回退或顺手整理用户已有修改。

## Directory Rules

保持文件分类清楚，不要把页面、图片、脚本乱放到根目录。

```txt
mars-y/
├─ AGENTS.md
├─ README.md
├─ index.html
├─ assets/
├─ blog/
│  ├─ index.html
│  ├─ assets/
│  └─ posts/
├─ pages/
├─ tools/
├─ scripts/
└─ .agents/
```

### Root

- `index.html`：只放站点首页。
- `README.md`：项目说明。
- `AGENTS.md`：给 AI agent 的项目规则。
- 根目录不要新增普通子页面 HTML。
- 根目录不要放文章图片、页面私有图片、下载产物、草稿或测试文件。

### assets/

- 放全站共用资源，例如 favicon、logo、全站图片。
- 只放多个页面都会复用的资源。
- 单篇文章或单个子页面专属图片不要放这里。

### blog/

- `blog/index.html`：博客首页和文章列表。
- `blog/assets/`：博客共用样式和博客级资源。
- `blog/posts/`：所有博客文章。

每篇博客必须单独一个文件夹：

```txt
blog/posts/yyyy-mm-dd-title/index.html
blog/posts/yyyy-mm-dd-title/images/
```

规则：

- 不要把文章 HTML 直接放在 `blog/posts/` 根下。
- 不要多篇文章共用同一个文章目录。
- 文章专属图片、截图、封面放入该文章目录下的 `images/`。
- 删除文章时，同时删除：
  - `blog/posts/.../`
  - `blog/index.html` 中对应入口
  - 首页或导航中对应链接

### pages/

普通静态子页面放这里。每个子页面必须单独开文件夹：

```txt
pages/page-slug/index.html
pages/page-slug/images/
```

适合放：

- 关于页
- 专题页
- 临时活动页
- 非博客、非工具的独立内容页

不要把这些页面散放到根目录。

### tools/

每个工具必须单独一个文件夹：

```txt
tools/tool-name/index.html
tools/tool-name/README.md
tools/tool-name/assets/
```

如果工具有脚本、样式、示例数据，优先放在该工具目录内。不要污染根目录或其它工具目录。

### scripts/

放仓库维护脚本，例如：

- 一键提交推送脚本
- 静态链接检查脚本
- 构建或部署辅助脚本

脚本默认从仓库根目录运行，执行前要输出将要处理的文件范围。

### .agents/

- `.agents/skills/`：项目级 repo skills。
- 每个 skill 必须有独立目录和 `SKILL.md`。
- 不要把 `.agents/skills/` 当成普通文档目录。

## New Page Rules

新增任何独立页面时，必须先判断类型：

- 博客文章：放到 `blog/posts/yyyy-mm-dd-title/index.html`
- 普通页面：放到 `pages/page-slug/index.html`
- 工具页面：放到 `tools/tool-name/index.html`

每个新页面都要有自己的目录。不要创建：

```txt
about.html
new-page.html
blog/posts/new-post.html
random-image.png
```

优先创建：

```txt
pages/about/index.html
blog/posts/2026-06-03-example-title/index.html
tools/example-tool/index.html
```

新增页面后同步更新相关入口：

- 站点首页：`index.html`
- 博客首页：`blog/index.html`
- 工具入口或导航链接
- README 中必要的访问路径说明

## Website Update Workflow

常规更新流程：

1. 读取相关文件和当前 diff。
2. 只修改当前任务相关文件。
3. 新页面必须单独建文件夹。
4. 检查链接是否指向真实路径。
5. 检查删除页面时是否同步删除入口链接。
6. 运行可用检查。
7. 提交并推送。

推荐状态检查：

```bash
git status --short --branch
git diff --check
```

如果只是把当前全部站点变更提交推送，可以使用：

```bash
bash scripts/update-ai-three-years-blog.sh "update site content"
```

注意：该脚本会提交全部工作区变更，包括新增、修改、删除。运行前必须先确认 `git status --short` 中没有不该提交的文件。

## Commit And Push Rules

- 提交前必须确认 `git status --short`。
- 不要把无关修改混进同一个 commit。
- 不要提交 `.env`、token、cookies、private keys、真实卡密、生成的压缩包或临时数据。
- 删除页面时，commit message 要说明删除对象。
- 推送默认使用：

```bash
git push origin main
```

Cloudflare Pages 已连接 GitHub 时，推送到 `main` 后会自动部署。

## Safety

不要读取、打印、提交或保存：

- `.env`
- GitHub token
- Cloudflare token
- OAuth token
- cookies
- private keys
- 密码
- 真实卡密文件
- CPA / SUB 输出文件
- 生成出来的 `.tar`、`.zip`、`.json`、`.txt` 数据文件

不要运行破坏性命令。不要删除用户内容，除非用户明确要求删除。

