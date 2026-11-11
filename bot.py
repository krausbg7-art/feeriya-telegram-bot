"""Автопостинг в Telegram-канал. Запускается GitHub Actions каждый час.
Публикует не более одного просроченного поста за запуск, в порядке номеров."""
import json, os, sys, uuid, datetime as dt, urllib.request

TOKEN = os.environ["TG_BOT_TOKEN"]
CHAT = os.environ.get("TG_CHAT_ID") or "@feeriya"
API = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"

posts = json.load(open("posts.json", encoding="utf-8"))
posted = json.load(open("posted.json"))
now = dt.datetime.now(dt.timezone.utc)

due = [p for p in posts if p["n"] not in posted
       and dt.datetime.fromisoformat(p["publish_at"]) <= now]
if not due:
    print("Нет постов к публикации"); sys.exit(0)
p = min(due, key=lambda x: x["n"])

def multipart(fields, fname, data):
    b = uuid.uuid4().hex
    out = b""
    for k, v in fields.items():
        out += f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode()
    out += (f'--{b}\r\nContent-Disposition: form-data; name="photo"; filename="{fname}"\r\n'
            f'Content-Type: image/png\r\n\r\n').encode() + data + f'\r\n--{b}--\r\n'.encode()
    return out, f"multipart/form-data; boundary={b}"

body, ctype = multipart({"chat_id": CHAT, "caption": p["text"][:1024]},
                        os.path.basename(p["image"]), open(p["image"], "rb").read())
req = urllib.request.Request(API, data=body, headers={"Content-Type": ctype})
with urllib.request.urlopen(req, timeout=120) as r:
    resp = json.load(r)
if not resp.get("ok"):
    sys.exit(f"Ошибка Telegram: {resp}")
posted.append(p["n"])
json.dump(sorted(posted), open("posted.json", "w"))
print(f"Опубликован пост {p['n']}: {p['title']}")
