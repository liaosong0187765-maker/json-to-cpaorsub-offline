# json-to-cpaorsub-offline

这个目录是 `mars-y` 站点下的一个子工具，用于在卡密 JSON/JSONL、CPA 压缩包和 SUB bundle 之间做本地格式转换。

## 文件

- `index.html`：网页版工具，发布后访问 `/tools/json-to-cpaorsub-offline/`。
- `minimal/`：最小运行版。
- `examples/card.example.jsonl`：示例输入。
- `card_to_cpa_sub.py`：把卡密 `txt/jsonl/json` 转换为 CPA `tar` 和 SUB `json`。
- `cpa_to_card_sub.py`：把 CPA 压缩包转换为卡密 JSONL 和 SUB `json`。
- `split_lines.py`：按行拆分 `.txt` 或 `.json` 文件。
- `SECURITY.md`：敏感数据注意事项。

## 网页版

发布后访问：

```txt
https://mars-y.com/tools/json-to-cpaorsub-offline/
```

也可以本地直接打开：

```txt
E:\ai\cloudflare\mars-y\tools\json-to-cpaorsub-offline\index.html
```

网页版是离线单文件工具，不需要安装依赖，也不会把内容上传到服务器。

## Python CLI

```powershell
cd E:\ai\cloudflare\mars-y\tools\json-to-cpaorsub-offline
python .\card_to_cpa_sub.py .\input.txt
python .\cpa_to_card_sub.py .\cpa.tar
python .\split_lines.py
```

## 最小运行版

最小运行版在：

```txt
minimal/
├─ index.html
└─ assets/
   ├─ favicon.ico
   └─ mars-y-icon.ico
```

## 安全提醒

这些工具处理的文件通常包含账号、OAuth token、邮箱等敏感信息。请只在本地可信环境使用，不要把真实卡密、CPA/SUB 输出、OAuth token、邮箱、密码、API Key 或生成数据文件提交到 GitHub。
