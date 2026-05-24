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

# Xtream / IPTV API settings (new)
XTV_USERNAME = "shanto4455"
XTV_PASSWORD = "01974264455"
XTV_DOMAIN = "http://tv.dgtv.xyz:8080"

XTV_URL_STREAMS = f"{XTV_DOMAIN}/player_api.php?username={XTV_USERNAME}&password={XTV_PASSWORD}&action=get_live_streams"
XTV_URL_CATEGORIES = f"{XTV_DOMAIN}/player_api.php?username={XTV_USERNAME}&password={XTV_PASSWORD}&action=get_live_categories"

# Auto section markers for live events
AUTO_START_MARKER = "#EXTM3U-LIVE-AUTO-START"
AUTO_END_MARKER = "#EXTM3U-LIVE-AUTO-END"

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
    """Yield channel blocks: (start_idx, end_idx_exclusive, extinf, headers(list), url or '')."""
    i, n = 0, len(lines)
    while i < n:
        if lines[i].startswith("#EXTINF:"):
            start = i
            extinf = lines[i]
            i += 1
            headers = []
            while i < n and (lines[i].startswith("#EXTVLCOPT:") or lines[i].startswith("#EXTHTTP:")):
                headers.append(lines[i])
                i += 1
            url = ""
            if i < n and lines[i].startswith("http"):
                url = lines[i]
                i += 1
            end = i
            yield (start, end, extinf, headers, url)
        else:
            i += 1

def get_name_from_extinf(extinf_line):
    m = re.search(r',\s*(.+?)\s*$', extinf_line.strip())
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

    # Build lookup: name -> (headers, url)
    src_map = {}
    for _, __, extinf, headers, url in iter_blocks(source_data):
        name = get_name_from_extinf(extinf).strip()
        if not name:
            continue
        src_map[name.lower()] = (headers, url)

    # Rewrite target blocks in template
    out = []
    i, n = 0, len(lines)
    while i < n:
        if lines[i].startswith("#EXTINF:"):
            block = next(iter_blocks(lines[i:]), None)
            if block:
                b_start, b_end, extinf, headers, url = block
                b_start += i
                b_end += i
                name = get_name_from_extinf(extinf).lower()
                if name in lower_targets and name in src_map:
                    new_headers, new_url = src_map[name]
                    out.append(extinf)
                    for h in new_headers:
                        out.append(h)
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

# =============== STEP 2 (NEW): Sync Cricket & Football live events ===============
def sync_live_events_into_template():
    """
    Xtream API থেকে শুধু 'Cricket live event' এবং 'Football live event'
    ক্যাটাগরির channel গুলো নিয়ে template.m3u-তে
    AUTO section হিসেবে inject করা হবে।
    """
    if not os.path.exists("template.m3u"):
        raise FileNotFoundError("template.m3u not found")

    # Televizo-style headers
    headers_req = {
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 9; Redmi S2 Build/PKQ1.180904.001)",
        "Accept": "*/*",
        "Connection": "Keep-Alive",
        "Accept-Encoding": "gzip",
        "X-Requested-With": "com.ottplay.ottplay"
    }

    # Fetch streams & categories
    streams = requests.get(XTV_URL_STREAMS, headers=headers_req, timeout=HTTP_TIMEOUT).json()
    categories = requests.get(XTV_URL_CATEGORIES, headers=headers_req, timeout=HTTP_TIMEOUT).json()

    # Map: category_id -> category_name
    category_map = {str(c["category_id"]): c.get("category_name", "") for c in categories}

    target_categories = {"cricket live event", "football live event"}

    auto_lines = []

    # Filter only target categories
    for ch in streams:
        name = ch.get("name", "").strip()
        stream_id = ch.get("stream_id")
        logo = ch.get("stream_icon", "") or ""
        category_id = str(ch.get("category_id", "")).strip()

        if not name or not stream_id:
            continue

        category_name = category_map.get(category_id, "").strip()
        if category_name.lower() not in target_categories:
            continue

        # Build stream URL
        stream_url = f"{XTV_DOMAIN}/live/{XTV_USERNAME}/{XTV_PASSWORD}/{stream_id}.m3u8"

        # EXTINF format: include logo + group-title = category_name
        extinf = f'#EXTINF:-1 tvg-logo="{logo}" group-title="{category_name}",{name}'
        auto_lines.append(extinf)
        auto_lines.append(stream_url)

    # Sort by category then name to keep it clean (optional)
    # not strictly necessary, but helps keep stable order
    # Here we already built auto_lines in original order; if you want sorted:
    # you could rebuild with sorting. To keep code simple, skipping sort step.

    # Inject into template.m3u between AUTO_START_MARKER and AUTO_END_MARKER
    lines = read_lines("template.m3u")

    new_lines = []
    i = 0
    n = len(lines)

    found_start = False
    found_end = False

    while i < n:
        line = lines[i]
        if line.strip() == AUTO_START_MARKER:
            found_start = True
            new_lines.append(AUTO_START_MARKER)

            # পুরনো section skip করে নতুন auto_lines বসাবে
            i += 1
            while i < n and lines[i].strip() != AUTO_END_MARKER:
                i += 1

            # এখন নতুন auto-lines insert
            new_lines.extend(auto_lines)

            # যদি end marker পাই, সেটাও যোগ করব
            if i < n and lines[i].strip() == AUTO_END_MARKER:
                found_end = True
                new_lines.append(AUTO_END_MARKER)
                i += 1
            continue
        else:
            new_lines.append(line)
            i += 1

    # যদি আগে কখনো marker না থাকে, তাহলে শেষে নতুন সেকশন add করব
    if not found_start or not found_end:
        # শেষ লাইনের পর একটা ফাঁকা লাইন দিতে পারো চাইলে
        if new_lines and new_lines[-1].strip() != "":
            new_lines.append("")
        new_lines.append(AUTO_START_MARKER)
        new_lines.extend(auto_lines)
        new_lines.append(AUTO_END_MARKER)

    write_lines("template.m3u", new_lines)
    print("✅ Live events (Cricket & Football) auto-section আপডেট হয়েছে।")

# =============== STEP 3: Final output with greeting ===============
def generate_final_file():
    input_file = 'template.m3u'
    output_file = 'ottrxs.m3u'

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
    # যেসব চ্যানেল Toffee সোর্স থেকে রিফ্রেশ করবেন
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
    safe_run("Live Events Sync", sync_live_events_into_template)
    safe_run("Final Output", generate_final_file)
