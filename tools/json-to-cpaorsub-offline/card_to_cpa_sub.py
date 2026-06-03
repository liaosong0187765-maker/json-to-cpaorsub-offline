import argparse
import base64
import io
import json
import re
import tarfile
from datetime import datetime, timezone, timedelta
from pathlib import Path


DEFAULT_CLIENT_ID = "app_EMoamEEZ73f0CkXaXp7hrann"
DEFAULT_PRIVACY_MODE = "training_off"
DEFAULT_PLAN_TYPE = "free"
CHUNK_SIZE = 100


def first_text(*values):
    for value in values:
        text = str(value or "").strip()
        if text:
            return text
    return ""


def read_object(value):
    return value if isinstance(value, dict) else {}


def coerce_timestamp(value):
    if isinstance(value, (int, float)):
        return max(0, int(value))
    text = str(value or "").strip()
    if not text:
        return 0
    if re.fullmatch(r"-?\d+", text):
        return max(0, int(text))
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        return max(0, int(parsed.timestamp()))
    except ValueError:
        return 0


def looks_like_email(value):
    text = str(value or "").strip()
    return bool(text and " " not in text and len(text.split("@")) == 2 and all(text.split("@")))


def b64url_encode_bytes(data):
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def b64url_decode_bytes(value):
    text = str(value or "").replace("-", "+").replace("_", "/")
    text += "=" * ((4 - len(text) % 4) % 4)
    return base64.b64decode(text)


def json_to_b64url(value):
    return b64url_encode_bytes(json.dumps(value, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))


def decode_jwt_payload(token):
    try:
        parts = str(token or "").split(".")
        if len(parts) < 2:
            return {}
        payload = json.loads(b64url_decode_bytes(parts[1]).decode("utf-8"))
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


def extract_auth(payload):
    return read_object(payload.get("https://api.openai.com/auth"))


def extract_profile(payload):
    return read_object(payload.get("https://api.openai.com/profile"))


def extract_account_id_from_auth(auth):
    account_id = first_text(auth.get("chatgpt_account_id"), auth.get("account_id"))
    if account_id:
        return account_id
    account_user_id = first_text(auth.get("chatgpt_account_user_id"))
    if "__" in account_user_id:
        return first_text(account_user_id.split("__")[-1])
    return ""


def extract_organization_id(id_auth, access_auth):
    direct = first_text(id_auth.get("organization_id"), access_auth.get("organization_id"))
    if direct:
        return direct
    organizations = id_auth.get("organizations")
    if isinstance(organizations, list) and organizations:
        preferred = next((org for org in organizations if isinstance(org, dict) and org.get("is_default")), organizations[0])
        return first_text(read_object(preferred).get("id"))
    return ""


def build_compatibility_id_token(account_id, user_id, organization_id, project_id, email, plan_type, client_id):
    now = int(datetime.now(tz=timezone.utc).timestamp())
    payload = {
        "aud": [first_text(client_id, DEFAULT_CLIENT_ID)],
        "email": first_text(email),
        "exp": now + 3600,
        "iat": now,
        "iss": "https://auth.openai.com",
        "https://api.openai.com/auth": {
            "account_id": first_text(account_id),
            "chatgpt_account_id": first_text(account_id),
            "chatgpt_user_id": first_text(user_id),
            "user_id": first_text(user_id),
            "organization_id": first_text(organization_id),
            "project_id": first_text(project_id),
            "chatgpt_plan_type": first_text(plan_type, DEFAULT_PLAN_TYPE),
        },
        "sub": first_text(user_id, account_id, "local-compat"),
    }
    return f"{json_to_b64url({'alg': 'RS256', 'typ': 'JWT', 'kid': 'compat'})}.{json_to_b64url(payload)}.{b64url_encode_bytes(b'local_compat_signature')}"


def ensure_id_token_claims(record):
    token = first_text(record.get("id_token"))
    account_id = first_text(record.get("chatgpt_account_id"))
    if not account_id:
        return token

    payload = decode_jwt_payload(token)
    if not payload:
        return build_compatibility_id_token(
            account_id,
            record.get("chatgpt_user_id"),
            record.get("organization_id"),
            first_text(record.get("project_id"), record.get("workspace_id")),
            first_text(record.get("email"), record.get("account_claims_email")),
            record.get("plan_type"),
            record.get("client_id"),
        )

    auth = dict(extract_auth(payload))
    existing_chatgpt_account_id = first_text(auth.get("chatgpt_account_id"))
    existing_account_id = first_text(auth.get("account_id"))
    if existing_chatgpt_account_id and existing_account_id:
        return token

    resolved_account_id = first_text(existing_chatgpt_account_id, existing_account_id, account_id)
    auth["chatgpt_account_id"] = first_text(existing_chatgpt_account_id, resolved_account_id)
    auth["account_id"] = first_text(existing_account_id, resolved_account_id)
    if record.get("chatgpt_user_id"):
        auth["chatgpt_user_id"] = first_text(auth.get("chatgpt_user_id"), auth.get("user_id"), record.get("chatgpt_user_id"))
        auth["user_id"] = first_text(auth.get("user_id"), auth.get("chatgpt_user_id"), record.get("chatgpt_user_id"))
    if record.get("organization_id") and not first_text(auth.get("organization_id")):
        auth["organization_id"] = record["organization_id"]
    if record.get("project_id") and not first_text(auth.get("project_id")):
        auth["project_id"] = record["project_id"]
    if record.get("plan_type") and not first_text(auth.get("chatgpt_plan_type")):
        auth["chatgpt_plan_type"] = record["plan_type"]

    parts = token.split(".")
    header = parts[0] if parts else json_to_b64url({"alg": "RS256", "typ": "JWT", "kid": "compat"})
    signature = parts[2] if len(parts) > 2 else b64url_encode_bytes(b"local_compat_signature")
    payload["https://api.openai.com/auth"] = auth
    return f"{header}.{json_to_b64url(payload)}.{signature}"


def finalize_record(record):
    item = dict(record)
    item["chatgpt_account_id"] = first_text(item.get("chatgpt_account_id"), item.get("account_id"))
    item["project_id"] = first_text(item.get("project_id"), item.get("workspace_id"))
    item["workspace_id"] = first_text(item.get("workspace_id"), item.get("project_id"))
    item["client_id"] = first_text(item.get("client_id"), DEFAULT_CLIENT_ID)
    item["plan_type"] = first_text(item.get("plan_type"), DEFAULT_PLAN_TYPE)
    item["privacy_mode"] = first_text(item.get("privacy_mode"), DEFAULT_PRIVACY_MODE)
    item["openai_oauth_responses_websockets_v2_enabled"] = bool(item.get("openai_oauth_responses_websockets_v2_enabled"))
    item["openai_oauth_responses_websockets_v2_mode"] = first_text(item.get("openai_oauth_responses_websockets_v2_mode"), "off")
    item["disabled"] = bool(item.get("disabled"))
    item["id_token"] = ensure_id_token_claims(item)
    return item


def normalize_record(input_item):
    item = read_object(input_item)
    if not item or isinstance(item.get("accounts"), list):
        return None

    tokens = read_object(item.get("tokens"))
    credentials = read_object(item.get("credentials"))
    extra = read_object(item.get("extra"))
    id_token = first_text(item.get("id_token"), credentials.get("id_token"), tokens.get("id_token"))
    access_token = first_text(item.get("access_token"), credentials.get("access_token"), tokens.get("access_token"))
    id_payload = decode_jwt_payload(id_token)
    access_payload = decode_jwt_payload(access_token)
    id_auth = extract_auth(id_payload)
    access_auth = extract_auth(access_payload)
    access_profile = extract_profile(access_payload)
    email = first_text(item.get("email"), extra.get("email"), credentials.get("email"), item.get("name"), id_payload.get("email"), access_profile.get("email"))
    login_identity = first_text(item.get("login_identity"))

    record = {
        "version": int(item.get("version") or 1),
        "platform": first_text(item.get("platform"), "chatgpt"),
        "email": email,
        "password": first_text(item.get("password")),
        "login_identity": login_identity,
        "phone": first_text(item.get("phone")),
        "access_token": access_token,
        "refresh_token": first_text(item.get("refresh_token"), credentials.get("refresh_token"), tokens.get("refresh_token")),
        "id_token": id_token,
        "session_token": first_text(item.get("session_token"), credentials.get("session_token")),
        "client_id": first_text(item.get("client_id"), credentials.get("client_id"), DEFAULT_CLIENT_ID),
        "chatgpt_account_id": first_text(item.get("chatgpt_account_id"), item.get("account_id"), credentials.get("chatgpt_account_id"), credentials.get("account_id"), extract_account_id_from_auth(id_auth), extract_account_id_from_auth(access_auth)),
        "chatgpt_user_id": first_text(item.get("chatgpt_user_id"), credentials.get("chatgpt_user_id"), id_auth.get("chatgpt_user_id"), id_auth.get("user_id"), access_auth.get("chatgpt_user_id"), access_auth.get("user_id")),
        "organization_id": first_text(item.get("organization_id"), credentials.get("organization_id"), extract_organization_id(id_auth, access_auth)),
        "project_id": first_text(item.get("project_id"), credentials.get("project_id"), item.get("workspace_id"), credentials.get("workspace_id"), id_auth.get("project_id"), access_auth.get("project_id")),
        "workspace_id": first_text(item.get("workspace_id"), credentials.get("workspace_id"), item.get("project_id"), credentials.get("project_id"), id_auth.get("project_id"), access_auth.get("project_id")),
        "created_at": coerce_timestamp(item.get("created_at")),
        "last_used": coerce_timestamp(item.get("last_used")),
        "status": first_text(item.get("status")),
        "source": first_text(item.get("source"), item.get("notes"), "codex_input" if tokens.get("access_token") else "sub_bundle_input" if credentials.get("access_token") else ""),
        "disabled": bool(item.get("disabled")),
        "account_claims_email": first_text(item.get("account_claims_email"), extra.get("email"), id_payload.get("email"), access_profile.get("email"), email),
        "plan_type": first_text(item.get("plan_type"), credentials.get("plan_type"), id_auth.get("chatgpt_plan_type"), access_auth.get("chatgpt_plan_type"), DEFAULT_PLAN_TYPE),
        "privacy_mode": first_text(item.get("privacy_mode"), extra.get("privacy_mode"), DEFAULT_PRIVACY_MODE),
        "openai_oauth_responses_websockets_v2_enabled": bool(item.get("openai_oauth_responses_websockets_v2_enabled") or extra.get("openai_oauth_responses_websockets_v2_enabled")),
        "openai_oauth_responses_websockets_v2_mode": first_text(item.get("openai_oauth_responses_websockets_v2_mode"), extra.get("openai_oauth_responses_websockets_v2_mode"), "off"),
    }
    if record["login_identity"] and not record["phone"] and not looks_like_email(record["login_identity"]):
        record["phone"] = record["login_identity"]
    if not record["email"]:
        record["email"] = first_text(record["account_claims_email"], record["chatgpt_account_id"], "unknown-account")
    return finalize_record(record)


def parse_input_items(text):
    trimmed = str(text or "").strip()
    if not trimmed:
        return []
    try:
        root = json.loads(trimmed)
    except json.JSONDecodeError:
        root = None

    if isinstance(root, dict):
        return [x for x in root.get("accounts", []) if isinstance(x, dict)] if isinstance(root.get("accounts"), list) else [root]
    if isinstance(root, list):
        return [x for x in root if isinstance(x, dict)]

    items = []
    for index, raw_line in enumerate(trimmed.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"第 {index} 行不是有效 JSON：{exc}") from exc
        if isinstance(parsed, dict):
            if isinstance(parsed.get("accounts"), list):
                items.extend(x for x in parsed["accounts"] if isinstance(x, dict))
            else:
                items.append(parsed)
    return items


def normalize_records_from_text(text):
    record_map = {}
    for item in parse_input_items(text):
        record = normalize_record(item)
        if not record:
            continue
        key = first_text(record.get("email"), record.get("chatgpt_account_id"), str(len(record_map))).lower()
        record_map[key] = record
    return list(record_map.values())


def to_iso_utc8(date):
    return date.astimezone(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S +0800")


def sanitize_filename(value, fallback):
    text = re.sub(r'[\\/:*?"<>|\x00-\x1f]+', "_", first_text(value, fallback))
    text = re.sub(r"\s+", "_", text).strip("._ ")
    return (text or fallback)[:90]


def stamp_now():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def chunks(items, size):
    for start in range(0, len(items), size):
        yield start // size + 1, items[start:start + size]


def build_cpa_payload(record, now):
    item = finalize_record(record)
    expires_at = coerce_timestamp(decode_jwt_payload(item.get("access_token")).get("exp"))
    return {
        "type": "codex",
        "email": item.get("email", ""),
        "expired": to_iso_utc8(datetime.fromtimestamp(expires_at, timezone.utc)) if expires_at else "",
        "id_token": item.get("id_token", ""),
        "account_id": first_text(item.get("chatgpt_account_id")),
        "disabled": bool(item.get("disabled")),
        "access_token": item.get("access_token", ""),
        "last_refresh": to_iso_utc8(now),
        "refresh_token": item.get("refresh_token", ""),
    }


def build_sub_account(record, now):
    item = finalize_record(record)
    expires_at = coerce_timestamp(decode_jwt_payload(item.get("access_token")).get("exp"))
    if not expires_at:
        expires_at = int(now.timestamp()) + 863999
    return {
        "name": item.get("email", ""),
        "platform": "openai",
        "type": "oauth",
        "credentials": {
            "access_token": item.get("access_token", ""),
            "chatgpt_account_id": item.get("chatgpt_account_id", ""),
            "chatgpt_user_id": item.get("chatgpt_user_id", ""),
            "client_id": first_text(item.get("client_id"), DEFAULT_CLIENT_ID),
            "email": item.get("email", ""),
            "expires_at": expires_at,
            "id_token": item.get("id_token", ""),
            "organization_id": item.get("organization_id", ""),
            "plan_type": first_text(item.get("plan_type"), DEFAULT_PLAN_TYPE),
            "refresh_token": item.get("refresh_token", ""),
        },
        "extra": {
            "email": item.get("email", ""),
            "openai_oauth_responses_websockets_v2_enabled": bool(item.get("openai_oauth_responses_websockets_v2_enabled")),
            "openai_oauth_responses_websockets_v2_mode": first_text(item.get("openai_oauth_responses_websockets_v2_mode"), "off"),
            "privacy_mode": first_text(item.get("privacy_mode"), DEFAULT_PRIVACY_MODE),
        },
        "concurrency": 10,
        "priority": 1,
        "rate_multiplier": 1,
        "auto_pause_on_expired": True,
    }


def write_cpa_tar(records, output_path, now):
    with tarfile.open(output_path, "w") as tar:
        for index, record in enumerate(records, start=1):
            payload = build_cpa_payload(record, now)
            data = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
            info = tarfile.TarInfo(f"{sanitize_filename(payload.get('email'), f'account_{index}')}.json")
            info.size = len(data)
            info.mtime = int(now.timestamp())
            tar.addfile(info, io.BytesIO(data))


def write_sub_json(records, output_path, now):
    bundle = {
        "exported_at": now.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        "proxies": [],
        "accounts": [build_sub_account(record, now) for record in records],
    }
    output_path.write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")


def convert(input_path):
    input_path = Path(input_path).expanduser().resolve()
    text = input_path.read_text(encoding="utf-8-sig")
    records = normalize_records_from_text(text)
    if not records:
        raise ValueError("输入文件里没有解析出有效账号记录")

    now = datetime.now(tz=timezone.utc)
    folder = input_path.parent
    stamp = stamp_now()
    outputs = []
    if len(records) <= CHUNK_SIZE:
        cpa_path = folder / f"cpa_{len(records)}_{stamp}.tar"
        sub_path = folder / f"sub_{len(records)}_{stamp}.json"
        write_cpa_tar(records, cpa_path, now)
        write_sub_json(records, sub_path, now)
        outputs.append((cpa_path, sub_path))
        return records, outputs

    for part, batch in chunks(records, CHUNK_SIZE):
        cpa_path = folder / f"cpa_{part:03d}_{len(batch)}_{stamp}.tar"
        sub_path = folder / f"sub_{part:03d}_{len(batch)}_{stamp}.json"
        write_cpa_tar(batch, cpa_path, now)
        write_sub_json(batch, sub_path, now)
        outputs.append((cpa_path, sub_path))
    return records, outputs


def print_outputs(records, outputs):
    print(f"已转换 {len(records)} 个账号")
    if len(outputs) > 1:
        print(f"已按每 {CHUNK_SIZE} 个账号拆分为 {len(outputs)} 份")
    for cpa_path, sub_path in outputs:
        print(f"CPA: {cpa_path}")
        print(f"SUB: {sub_path}")


def should_continue():
    answer = input("还需要继续转换吗？输入 y/是 继续，直接回车退出：").strip().lower()
    return answer in {"y", "yes", "是", "继续"}


def run_once(input_file):
    records, outputs = convert(input_file)
    print_outputs(records, outputs)


def main():
    parser = argparse.ArgumentParser(description="把卡密/JSON/JSONL 转换为 cpa.tar 和 SUB bundle。")
    parser.add_argument("input", nargs="?", help="卡密 txt/jsonl/json 文件路径")
    args = parser.parse_args()
    if args.input:
        run_once(args.input)
        return

    while True:
        input_file = input("请输入卡密 txt/jsonl/json 文件路径：").strip().strip('"')
        if not input_file:
            print("未输入文件路径，已退出。")
            return
        try:
            run_once(input_file)
        except Exception as exc:
            print(f"转换失败：{exc}")
        if not should_continue():
            print("已退出。")
            return


if __name__ == "__main__":
    main()
