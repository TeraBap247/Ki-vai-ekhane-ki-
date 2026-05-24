import os
import re
import requests
from datetime import datetime, timedelta

try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None


# =============== SETTINGS ===============
HTTP_TIMEOUT = 20


# =============== UTILS ===============
def safe_run(section, fn):
    try:
        fn()
    except Exception as e:
        print(f"[{section}] তে সমস্যা হয়েছে: {e}")


def read_lines(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read().splitlines()


def write_lines(path, lines):
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip("\n") + "\n")


def iter_blocks(lines):
    i, n = 0, len(lines)
    while i < n:
        if lines[i].startswith("#EXTINF:"):
            start = i
            extinf = lines[i]
            i += 1
            headers = []

            while i < n and (
                lines[i].startswith("#EXTVLCOPT:")
                or lines[i].startswith("#EXTHTTP:")
            ):
                headers.append(lines[i])
                i += 1

            url = ""
            if i < n and lines[i].startswith("http"):
                url = lines[i]
                i += 1

            end = i
            yield start, end, extinf, headers, url
        else:
            i += 1


def get_name_from_extinf(extinf_line):
    m = re.search(r",\s*(.+?)\s*$", extinf_line.strip())
    return m.group(1).strip() if m else ""


# =============== STEP 1: Selected channels refresh from Toffee source ===============
def update_channels(channel_names):
    source_url = "https://raw.githubusercontent.com/BINOD-XD/Toffee-Auto-Update-Playlist/refs/heads/main/toffee_OTT_Navigator.m3u"

    r = requests.get(source_url, timeout=HTTP_TIMEOUT)
    r.raise_for_status()
    source_data = r.text.splitlines()

    if not os.path.exists("template.m3u"):
        raise FileNotFoundError("template.m3u not found")

    lines = read_lines("template.m3u")
    lower_targets = [c.lower() for c in channel_names]

    src_map = {}
    for _, __, extinf, headers, url in iter_blocks(source_data):
        name = get_name_from_extinf(extinf).strip()
        if name:
            src_map[name.lower()] = (headers, url)

    out = []
    i, n = 0, len(lines)

    while i < n:
        if lines[i].startswith("#EXTINF:"):
            block = next(iter_blocks(lines[i:]), None)

            if block:
                b_start, b_end, extinf, headers, url = block
                b_end += i

                name = get_name_from_extinf(extinf).lower()

                if name in lower_targets and name in src_map:
                    new_headers, new_url = src_map[name]

                    out.append(extinf)
                    out.extend(new_headers)

                    if new_url:
                        out.append(new_url)

                    i = b_end
                    continue
                else:
                    out.extend(lines[i:b_end])
                    i = b_end
                    continue

        out.append(lines[i])
        i += 1

    write_lines("template.m3u", out)
    print("✅ Toffee চ্যানেল রিফ্রেশ সম্পন্ন হয়েছে।")


# =============== STEP 2: Final output with greeting ===============
def generate_final_file():
    input_file = "template.m3u"
    output_file = "ottrxs.m3u"

    if ZoneInfo:
        bd_time = datetime.now(ZoneInfo("Asia/Dhaka"))
    else:
        bd_time = datetime.utcnow() + timedelta(hours=6)

    hour = bd_time.hour

    if 5 <= hour < 12:
        msg = "🥱Good morning☀️👉Vip Ip Tv By Reyad Hossain🇧🇩"
    elif 12 <= hour < 18:
        msg = "☀️Good Afternoon👉Vip Ip Tv By Reyad Hossain🇧🇩"
    else:
        msg = "🌙Good Night👉Vip Ip Tv By Reyad Hossain🇧🇩"

    if not os.path.exists(input_file):
        raise FileNotFoundError("template.m3u not found")

    src = read_lines(input_file)
    out = []

    for i, line in enumerate(src):
        if i == 0 and line.startswith("#EXTM3U"):
            out.append(f'#EXTM3U billed-msg="{msg}"')
        else:
            out.append(line)

    write_lines(output_file, out)
    print("🎉 Final M3U তৈরি হয়েছে:", output_file)


# =============== DRIVER ===============
if __name__ == "__main__":
    channel_list = [
        "Cartoon Network",
        "Pogo",
        "Discovery Kids",
        "Cartoon Network HD",
        "ICC Women's Cricket World Cup 2025",
        "TLC HD",
        "EPL channel 1",
        "BFL Live 1",
        "SONY BBC EARTH HD VIP",
        "Discovery"
    ]

    safe_run("Toffee Channel Refresh", lambda: update_channels(channel_list))
    safe_run("Final Output", generate_final_file)