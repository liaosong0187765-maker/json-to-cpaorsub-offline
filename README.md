# json_to_cpaorsub

用于在卡密 JSON/JSONL、CPA 压缩包和 SUB bundle 之间做本地格式转换的离线工具集。

## 下载

- 完整项目：https://github.com/liaosong0187765-maker/json-to-cpaorsub-offline
- 最小运行版：https://github.com/liaosong0187765-maker/json-to-cpaorsub-offline/tree/main/minimal

最小运行版只需要下载 `minimal/` 目录，保持下面结构不变后双击打开 `index.html`：

```txt
minimal/
├─ index.html
└─ assets/
   ├─ favicon.ico
   └─ mars-y-icon.ico
```

## 功能

- `index.html`：单文件网页版，本地浏览器直接打开即可使用。
- `minimal/`：网页版最小运行包，只包含 HTML 和图标资源。
- `card_to_cpa_sub.py`：把卡密 `txt/jsonl/json` 转换为 CPA `tar` 和 SUB `json`。
- `cpa_to_card_sub.py`：把 CPA 压缩包转换为卡密 JSONL 和 SUB `json`，支持 `.tar`、`.tar.gz`、`.tgz`、`.zip`。
- `split_lines.py`：把 `.txt` 或 `.json` 文件按每 100 行拆分。

## 环境要求

- Python 3.10+
- 仅使用 Python 标准库，无需安装第三方依赖。

## 使用方法

### 网页版

直接双击打开 `index.html`，或用浏览器打开。

网页版是离线单文件工具，不需要安装依赖，也不会把内容上传到服务器。可以直接粘贴内容，也可以点击“读取文件”选择本地 `.txt`、`.json` 或 `.jsonl` 文件。

新版网页支持读取多个文档或文件夹：输入框只预览第一个文件，导出时会先逐个解析全部文件并合并记录。`每份` 留空表示全部合并为一个文件；填写 `50` 表示每 50 条记录导出一份，剩余记录会自动作为最后一份导出。

### GitHub Pages 部署

本项目所有文件都放在仓库根目录。上传到 GitHub 后，在仓库设置里开启 Pages：

1. 打开 `Settings` -> `Pages`
2. `Source` 选择 `Deploy from a branch`
3. `Branch` 选择 `main`，目录选择 `/root`
4. 保存后访问 GitHub Pages 生成的网址

### 卡密转 CPA 和 SUB

```powershell
python .\card_to_cpa_sub.py .\input.txt
```

也可以不传参数，按提示输入文件路径：

```powershell
python .\card_to_cpa_sub.py
```

转换结果会输出到输入文件所在目录：

- `cpa_<数量>_<时间>.tar`
- `sub_<数量>_<时间>.json`

超过 100 条账号时会自动分批输出。

### CPA 转卡密和 SUB

```powershell
python .\cpa_to_card_sub.py .\cpa.tar
```

转换结果会输出到输入文件所在目录：

- `卡密_<数量>_<时间>.txt`
- `sub_<数量>_<时间>.json`

注意：CPA 包不包含密码、手机号等字段，反向生成的卡密记录中这些字段会留空。

### 拆分大文件

```powershell
python .\split_lines.py
```

按提示输入 `.txt` 或 `.json` 文件路径。程序会在同名目录中生成拆分后的文件。

## 输入数据提醒

这些工具处理的文件通常包含账号、OAuth token、邮箱等敏感信息。请只在本地可信环境使用。

不要把以下内容提交到 GitHub：

- 真实卡密文件
- 真实 CPA/SUB 输出文件
- OAuth access token、refresh token、id token
- 邮箱列表、密码、API Key、应用专用密码
- 生成出来的 `.tar`、`.zip`、`.json`、`.txt` 数据文件

## 开源协议

MIT License
