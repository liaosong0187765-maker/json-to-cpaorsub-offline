import argparse
import base64
import json
import re
import tarfile
import zipfile
from io import BytesIO
from datetime import datetime, timezone
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


def b64url_decode_bytes(value):
    text = str(value or "").replace("-", "+").replace("_", "/")
    text += "=" * ((4 - len(text) % 4) % 4)
    return base64.b64decode(text)


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


def cpa_to_card_record(payload):
    id_token = first_text(payload.get("id_token"))
    access_token = first_text(payload.get("access_token"))
    id_payload = decode_jwt_payload(id_token)
    access_payload = decode_jwt_payload(access_token)
    id_auth = extract_auth(id_payload)
    access_auth = extract_auth(access_payload)
    access_profile = extract_profile(access_payload)
    email = first_text(payload.get("email"), id_payload.get("email"), access_profile.get("email"), "unknown-account")
    account_id = first_text(payload.get("account_id"), extract_account_id_from_auth(id_auth), extract_account_id_from_auth(access_auth))
    user_id = first_text(id_auth.get("chatgpt_user_id"), id_auth.get("user_id"), access_auth.get("chatgpt_user_id"), access_auth.get("user_id"))
    organization_id = extract_organization_id(id_auth, access_auth)
    now_ts = int(datetime.now(tz=timezone.utc).timestamp())
    return {
        "version": 1,
        "platform": "chatgpt",
        "email": email,
        "password": "",
        "login_identity": email,
        "phone": "",
        "access_token": access_token,
        "refresh_token": first_text(payload.get("refresh_token")),
        "id_token": id_token,
        "session_token": "",
        "client_id": DEFAULT_CLIENT_ID,
        "chatgpt_account_id": account_id,
        "chatgpt_user_id": user_id,
        "organization_id": organization_id,
        "project_id": account_id,
        "workspace_id": account_id,
        "created_at": now_ts,
        "last_used": now_ts,
        "status": "registered",
        "source": "cpa_tar_input",
        "account_claims_email": email,
        "plan_type": first_text(id_auth.get("chatgpt_plan_type"), access_auth.get("chatgpt_plan_type"), DEFAULT_PLAN_TYPE),
        "privacy_mode": DEFAULT_PRIVACY_MODE,
        "openai_oauth_responses_websockets_v2_enabled": False,
        "openai_oauth_responses_websockets_v2_mode": "off",
        "disabled": bool(payload.get("disabled")),
    }


def build_sub_account(record):
    expires_at = coerce_timestamp(decode_jwt_payload(record.get("access_token")).get("exp"))
    if not expires_at:
        expires_at = int(datetime.now(tz=timezone.utc).timestamp()) + 863999
    return {
        "name": record.get("email", ""),
        "platform": "openai",
        "type": "oauth",
        "credentials": {
            "access_token": record.get("access_token", ""),
            "chatgpt_account_id": record.get("chatgpt_account_id", ""),
            "chatgpt_user_id": record.get("chatgpt_user_id", ""),
            "client_id": first_text(record.get("client_id"), DEFAULT_CLIENT_ID),
            "email": record.get("email", ""),
            "expires_at": expires_at,
            "id_token": record.get("id_token", ""),
            "organization_id": record.get("organization_id", ""),
            "plan_type": first_text(record.get("plan_type"), DEFAULT_PLAN_TYPE),
            "refresh_token": record.get("refresh_token", ""),
        },
        "extra": {
            "email": record.get("email", ""),
            "openai_oauth_responses_websockets_v2_enabled": bool(record.get("openai_oauth_responses_websockets_v2_enabled")),
            "openai_oauth_responses_websockets_v2_mode": first_text(record.get("openai_oauth_responses_websockets_v2_mode"), "off"),
            "privacy_mode": first_text(record.get("privacy_mode"), DEFAULT_PRIVACY_MODE),
        },
        "concurrency": 10,
        "priority": 1,
        "rate_multiplier": 1,
        "auto_pause_on_expired": True,
    }


def stamp_now():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def chunks(items, size):
    for start in range(0, len(items), size):
        yield start // size + 1, items[start:start + size]


def append_cpa_payload(records, payload):
    if isinstance(payload, dict):
        records.append(cpa_to_card_record(payload))
    elif isinstance(payload, list):
        for item in payload:
            if isinstance(item, dict):
                records.append(cpa_to_card_record(item))


def read_cpa_tar(input_path):
    records = []
    with tarfile.open(input_path, "r:*") as tar:
        for member in tar.getmembers():
            if not member.isfile() or not member.name.lower().endswith(".json"):
                continue
            file_obj = tar.extractfile(member)
            if file_obj is None:
                continue
            payload = json.loads(file_obj.read().decode("utf-8-sig"))
            append_cpa_payload(records, payload)
    return records


def read_cpa_tar_bytes(data):
    records = []
    with tarfile.open(fileobj=BytesIO(data), mode="r:*") as tar:
        for member in tar.getmembers():
            if not member.isfile() or not member.name.lower().endswith(".json"):
                continue
            file_obj = tar.extractfile(member)
            if file_obj is None:
                continue
            payload = json.loads(file_obj.read().decode("utf-8-sig"))
            append_cpa_payload(records, payload)
    return records


def read_cpa_zip(input_path):
    records = []
    with zipfile.ZipFile(input_path) as archive:
        for name in archive.namelist():
            lower_name = name.lower()
            if lower_name.endswith("/") or lower_name.startswith("__macosx/"):
                continue
            data = archive.read(name)
            if lower_name.endswith(".json"):
                payload = json.loads(data.decode("utf-8-sig"))
                append_cpa_payload(records, payload)
            elif lower_name.endswith((".tar", ".tar.gz", ".tgz")):
                records.extend(read_cpa_tar_bytes(data))
    return records


def read_cpa_archive(input_path):
    if zipfile.is_zipfile(input_path):
        return read_cpa_zip(input_path)
    if tarfile.is_tarfile(input_path):
        return read_cpa_tar(input_path)
    raise ValueError("不支持的压缩包格式：请提供 .tar、.tar.gz、.tgz 或 .zip 文件")


def write_card_file(records, output_path):
    text = "\n".join(json.dumps(record, ensure_ascii=False) for record in records)
    output_path.write_text(text + ("\n" if text else ""), encoding="utf-8")


def write_sub_json(records, output_path):
    bundle = {
        "exported_at": datetime.now(tz=timezone.utc).isoformat().replace("+00:00", "Z"),
        "proxies": [],
        "accounts": [build_sub_account(record) for record in records],
    }
    output_path.write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")


def convert(input_path):
    input_path = Path(input_path).expanduser().resolve()
    records = read_cpa_archive(input_path)
    if not records:
        raise ValueError("压缩包里没有解析出 CPA JSON 账号")

    folder = input_path.parent
    stamp = stamp_now()
    outputs = []
    if len(records) <= CHUNK_SIZE:
        card_path = folder / f"卡密_{len(records)}_{stamp}.txt"
        sub_path = folder / f"sub_{len(records)}_{stamp}.json"
        write_card_file(records, card_path)
        write_sub_json(records, sub_path)
        outputs.append((card_path, sub_path))
        return records, outputs

    for part, batch in chunks(records, CHUNK_SIZE):
        card_path = folder / f"卡密_{part:03d}_{len(batch)}_{stamp}.txt"
        sub_path = folder / f"sub_{part:03d}_{len(batch)}_{stamp}.json"
        write_card_file(batch, card_path)
        write_sub_json(batch, sub_path)
        outputs.append((card_path, sub_path))
    return records, outputs


def print_outputs(records, outputs):
    print(f"已转换 {len(records)} 个账号")
    if len(outputs) > 1:
        print(f"已按每 {CHUNK_SIZE} 个账号拆分为 {len(outputs)} 份")
    for card_path, sub_path in outputs:
        print(f"卡密: {card_path}")
        print(f"SUB: {sub_path}")
    print("提示：CPA 包不包含密码、手机号等字段，反向卡密中这些字段会留空。")


def should_continue():
    answer = input("还需要继续转换吗？输入 y/是 继续，直接回车退出：").strip().lower()
    return answer in {"y", "yes", "是", "继续"}


def run_once(input_file):
    records, outputs = convert(input_file)
    print_outputs(records, outputs)


def main():
    parser = argparse.ArgumentParser(description="把 CPA 压缩包转换为卡密 JSONL 和 SUB bundle。")
    parser.add_argument("input", nargs="?", help="CPA 压缩包路径，支持 .tar/.tar.gz/.tgz/.zip")
    args = parser.parse_args()
    if args.input:
        run_once(args.input)
        return

    while True:
        input_file = input("请输入 CPA 压缩包文件路径：").strip().strip('"')
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
