import argparse
import json
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import requests

from config import BASE_DIR
from vk_bot import create_vk_api


def iter_save_messages_photo_payloads(upload_payload):
    if upload_payload.get("photo"):
        yield upload_payload
        return

    files_payload = upload_payload.get("files")
    if not files_payload:
        yield upload_payload
        return

    file_values = list(files_payload.values())
    common = {
        "server": upload_payload.get("server"),
        "hash": upload_payload.get("hash"),
    }
    yield {**common, "photo": json.dumps(files_payload, ensure_ascii=False)}
    yield {**common, "photo": json.dumps(file_values, ensure_ascii=False)}
    yield {**common, "photos_list": json.dumps(files_payload, ensure_ascii=False)}
    yield {**common, "photos_list": json.dumps(file_values, ensure_ascii=False)}


def save_message_photos(vk, upload_payload):
    last_error = None
    for index, save_payload in enumerate(iter_save_messages_photo_payloads(upload_payload), start=1):
        print(f"save_variant_{index}={save_payload}")
        try:
            uploaded = vk.photos.saveMessagesPhoto(**save_payload)
        except Exception as error:
            last_error = error
            print(f"save_variant_{index}_error={error}")
            continue
        print(f"save_variant_{index}_ok=True")
        return uploaded
    if last_error:
        raise last_error
    return []

def main():
    parser = argparse.ArgumentParser(description="Test VK message photo upload from a local file.")
    parser.add_argument("photo_path", help="Photo path relative to the project root, for example storage/photos/147991194/1.jpg")
    parser.add_argument("--peer-id", required=True, type=int, help="VK user_id or chat peer_id to create a message upload server for.")
    parser.add_argument("--send", action="store_true", help="Also send the uploaded attachment to --peer-id.")
    args = parser.parse_args()

    absolute_path = BASE_DIR / Path(args.photo_path.replace("\\", "/"))
    print(f"project_root={BASE_DIR}")
    print(f"photo_path={absolute_path}")
    print(f"photo_exists={absolute_path.exists()}")
    if not absolute_path.exists():
        raise SystemExit(2)

    vk = create_vk_api()
    upload_server = vk.photos.getMessagesUploadServer(peer_id=args.peer_id)
    print(f"upload_server={upload_server}")
    with absolute_path.open("rb") as photo_file:
        raw_response = requests.post(
            upload_server["upload_url"],
            files={"file1": (absolute_path.name, photo_file, "image/jpeg")},
            timeout=60,
        )
    print(f"upload_status_code={raw_response.status_code}")
    print(f"upload_text={raw_response.text[:2000]}")
    upload_payload = raw_response.json()

    uploaded = save_message_photos(vk, upload_payload)
    print(f"uploaded={uploaded}")

    attachments = []
    for item in uploaded:
        owner_id = item.get("owner_id")
        photo_id = item.get("id")
        access_key = item.get("access_key")
        if owner_id is None or photo_id is None:
            continue
        token = f"photo{owner_id}_{photo_id}"
        if access_key:
            token = f"{token}_{access_key}"
        attachments.append(token)

    attachment = ",".join(attachments)
    print(f"attachment={attachment}")

    if args.send:
        response = vk.messages.send(
            peer_id=args.peer_id,
            message="photo upload test",
            random_id=0,
            attachment=attachment,
        )
        print(f"send_response={response}")


if __name__ == "__main__":
    main()
