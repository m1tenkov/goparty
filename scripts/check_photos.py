from pathlib import Path

from config import BASE_DIR
from database import connection


def main():
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                u.vk_user_id,
                up.sort_order,
                up.photo_path,
                up.vk_photo_token
            FROM user_photos up
            JOIN users u ON u.id = up.user_id
            ORDER BY u.vk_user_id, up.sort_order
            """
        )
        rows = cursor.fetchall()

    missing = []
    tokenless = []
    for row in rows:
        photo_path = row["photo_path"]
        absolute_path = BASE_DIR / Path(str(photo_path).replace("\\", "/"))
        exists = absolute_path.exists()
        has_token = bool(row.get("vk_photo_token"))
        status = "OK" if exists else "MISSING"
        token_status = "token" if has_token else "no_token"
        print(f"{status:7} {token_status:8} vk={row['vk_user_id']} sort={row['sort_order']} path={photo_path}")
        if not exists:
            missing.append(row)
        if not has_token:
            tokenless.append(row)

    print()
    print(f"total_photos={len(rows)}")
    print(f"missing_files={len(missing)}")
    print(f"without_vk_token={len(tokenless)}")


if __name__ == "__main__":
    main()
