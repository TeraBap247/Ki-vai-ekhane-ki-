import os
import re
import difflib
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

XTV_URL_STREAMS = (
    f"{XTV_DOMAIN}/player_api.php?username={XTV_USERNAME}"
    f"&password={XTV_PASSWORD}&action=get_live_streams"
)
XTV_URL_CATEGORIES = (
    f"{XTV_DOMAIN}/player_api.php?username={XTV_USERNAME}"
    f"&password={XTV_PASSWORD}&action=get_live_categories"
)

# Auto section markers for live events
AUTO_START_MARKER = "#EXTM3U-LIVE-AUTO-START"
AUTO_END_MARKER = "#EXTM3U-LIVE-AUTO-END"

# =============== IGNORE CHANNELS (শুধু Xtream normal sync এর জন্য) ===============
# NOTE: Cricket / Football Live Event auto-section এ এগুলোর কোন প্রভাব নেই
IGNORE_CHANNELS = {
    "cartoon network",
    "pogo",
    "discovery kids",
    "cartoon network hd",
    "icc women's cricket world cup 2025",
    "tlc hd",
    "epl channel 1",
    "bfl live 1",
    "sony bbc earth hd vip",
    "discovery",
    "star jalsha hd",
    "star jalsha sd",
    "zee bangla hd",
    "zee bangla sd",
    "sony sports ten 5 hd",
    "disney xd",
    "mr bean",
    "hbo hits",
    "bein sports mena english 1",
    "bein sports mena english 2",
    "bein sports mena english 3",
    "bein sports mena 9",
    "bein sports xtra 1",
    "bein sports xtra 2",
    "dazn 1 hd",
    "dazn 2 hd",
    "dazn 3 hd",
    "dazn 4 hd",
    "fashion tv",
    "star gold thrills",
    "colors cineplex bollywood",
    "colors cineplex hd",
    "sony wah",
    "colors infinity hd",
    "tyc sports argentina",
    "btv news",
    "songsad tv",
    "sananda tv",
    "biswa bangla 24",
    "alpona tv",
    "deshi tv",
    "deshe bideshe",
    "channel 52 usa",
    "movie plus",
    "btv world",
    "movies action",
    "nan tv",
    "makkah live quran tv",
    "madina live tv sunnah tv",
    "channel 5",
}
IGNORE_CHANNELS = {c.lower().strip() for c in IGNORE_CHANNELS}

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
    """
    Yield channel blocks: (start_idx, end_idx_exclusive, extinf, headers(list), url or '').
    """
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


def replace_name_in_extinf(extinf_line, new_name):
    return re.sub(r',\s*(.+?)\s*$', f",{new_name}", extinf_line.strip())


def normalize_name(name: str) -> str:
    """
    নাম match করার জন্য লাইট normalization:
    - lowercase
    - HD / SD / VIP / TV / Channel / Sports ইত্যাদি common শব্দ কেটে ফেলে
    - non-alphanumeric সবকিছু space
    """
    s = name.lower()
    # কিছু common শব্দ drop করা
    remove_words = [
        " hd", " sd", " vip", " full hd", " ultra hd",
        " channel", " tv", " sports"
    ]
    for w in remove_words:
        s = s.replace(w, " ")
    s = s.replace("&", " and ")
    s = re.sub(r'[^a-z0-9]+', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

# =============== STEP 1: Selected channels refresh from Toffee source ===============

def update_channels(channel_names):
    source_url = (
        "https://raw.githubusercontent.com/BINOD-XD/"
        "Toffee-Auto-Update-Playlist/refs/heads/main/toffee_OTT_Navigator.m3u"
    )
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

# =============== STEP 2 (NEW): Xtream normal channels (BDIX/CDN priority) ===============

def sync_xtream_bdix_cdn_into_template():
    """
    Xtream/IPTV API থেকে BDIX / CDN ক্যাটাগরির channel গুলো দিয়ে
    template.m3u এর normal চ্যানেলের stream link আপডেট করবে।

    - IGNORE_CHANNELS এ থাকা নামগুলো skip করবে
    - AUTO_START_MARKER–AUTO_END_MARKER এর মধ্যে কিছুই বদলাবে না
    - আগে BDIX ক্যাটাগরি থেকে খুঁজবে, না পেলে CDN থেকে
    - একাধিক stream match পেলে অতিরিক্তগুলোকে "Name 2", "Name 3" ইত্যাদি নাম দিয়ে add করবে
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

    streams = requests.get(XTV_URL_STREAMS, headers=headers_req, timeout=HTTP_TIMEOUT).json()
    categories = requests.get(XTV_URL_CATEGORIES, headers=headers_req, timeout=HTTP_TIMEOUT).json()

    category_map = {str(c["category_id"]): c.get("category_name", "") for c in categories}

    # index: { "BDIX": {norm_name: [stream,...]}, "CDN": {...} }
    xtream_index = {"BDIX": {}, "CDN": {}}

    for ch in streams:
        name = ch.get("name", "").strip()
        if not name:
            continue
        stream_id = ch.get("stream_id")
        if not stream_id:
            continue

        category_id = str(ch.get("category_id", "")).strip()
        cat_name = category_map.get(category_id, "").strip()

        upper_cat = cat_name.upper()
        if upper_cat.startswith("BDIX"):
            key = "BDIX"
        elif upper_cat.startswith("CDN"):
            key = "CDN"
        else:
            continue

        norm = normalize_name(name)
        xtream_index[key].setdefault(norm, []).append(ch)

    lines = read_lines("template.m3u")
    new_lines = []

    i = 0
    n = len(lines)
    in_auto_section = False

    while i < n:
        line = lines[i]

        # AUTO section untouched
        if line.strip() == AUTO_START_MARKER:
            in_auto_section = True
            new_lines.append(line)
            i += 1
            continue
        if line.strip() == AUTO_END_MARKER:
            in_auto_section = False
            new_lines.append(line)
            i += 1
            continue

        if not in_auto_section and line.startswith("#EXTINF:"):
            block = next(iter_blocks(lines[i:]), None)
            if block:
                b_start, b_end, extinf, headers, url = block
                b_start += i
                b_end += i

                chan_name = get_name_from_extinf(extinf)
                chan_name_lower = chan_name.lower().strip()

                # ignore list এ থাকলে কিছু করবে না
                if chan_name_lower in IGNORE_CHANNELS:
                    new_lines.extend(lines[i:b_end])
                    i = b_end
                    continue

                norm_name = normalize_name(chan_name)

                # direct match BDIX > CDN
                matches = xtream_index["BDIX"].get(norm_name)
                if not matches:
                    matches = xtream_index["CDN"].get(norm_name)

                # direct না পেলে fuzzy match try
                if not matches:
                    best_ratio = 0.0
                    best_matches = None

                    for key in ("BDIX", "CDN"):
                        for norm_key, lst in xtream_index[key].items():
                            ratio = difflib.SequenceMatcher(None, norm_name, norm_key).ratio()
                            if ratio > best_ratio:
                                best_ratio = ratio
                                best_matches = lst

                    if best_ratio >= 0.8:
                        matches = best_matches

                if not matches:
                    # কনো match না পেলে original block রেখে দিচ্ছি
                    new_lines.extend(lines[i:b_end])
                    i = b_end
                    continue

                # এখন matches আছে → প্রথমটা original নামে, বাকিগুলো Name 2, Name 3...
                first = True
                counter = 1

                for ch in matches:
                    stream_id = ch.get("stream_id")
                    if not stream_id:
                        continue

                    stream_url = f"{XTV_DOMAIN}/live/{XTV_USERNAME}/{XTV_PASSWORD}/{stream_id}.m3u8"

                    if first:
                        # existing block কে replace করছি: extinf + headers + নতুন url
                        new_lines.append(extinf)
                        for h in headers:
                            new_lines.append(h)
                        new_lines.append(stream_url)
                        first = False
                        counter = 2
                    else:
                        # duplicate channel: Name 2, Name 3...
                        dup_name = f"{chan_name} {counter}"
                        new_extinf = replace_name_in_extinf(extinf, dup_name)
                        new_lines.append(new_extinf)
                        for h in headers:
                            new_lines.append(h)
                        new_lines.append(stream_url)
                        counter += 1

                i = b_end
                continue

        # default: normal line
        new_lines.append(line)
        i += 1

    write_lines("template.m3u", new_lines)
    print("✅ Xtream normal channels (BDIX/CDN) sync সম্পন্ন হয়েছে।")

# =============== STEP 3: Sync Cricket & Football live events ===============

def sync_live_events_into_template():
    """
    Xtream API থেকে শুধু 'Cricket live event' এবং 'Football live event'
    ক্যাটাগরির channel গুলো নিয়ে template.m3u-তে AUTO section হিসেবে inject করা হবে।
    IGNORE_CHANNELS এখানে apply হবে না।
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

    streams = requests.get(XTV_URL_STREAMS, headers=headers_req, timeout=HTTP_TIMEOUT).json()
    categories = requests.get(XTV_URL_CATEGORIES, headers=headers_req, timeout=HTTP_TIMEOUT).json()

    category_map = {str(c["category_id"]): c.get("category_name", "") for c in categories}
    target_categories = {"cricket live event", "football live event"}

    auto_lines = []

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

        stream_url = f"{XTV_DOMAIN}/live/{XTV_USERNAME}/{XTV_PASSWORD}/{stream_id}.m3u8"
        extinf = f'#EXTINF:-1 tvg-logo="{logo}" group-title="{category_name}",{name}'
        auto_lines.append(extinf)
        auto_lines.append(stream_url)

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

            i += 1
            # পুরোনো auto section skip
            while i < n and lines[i].strip() != AUTO_END_MARKER:
                i += 1

            # নতুন auto lines বসানো
            new_lines.extend(auto_lines)

            if i < n and lines[i].strip() == AUTO_END_MARKER:
                found_end = True
                new_lines.append(AUTO_END_MARKER)
                i += 1
            continue
        else:
            new_lines.append(line)
            i += 1

    # আগে marker না থাকলে শেষে add করবে
    if not found_start or not found_end:
        if new_lines and new_lines[-1].strip() != "":
            new_lines.append("")
        new_lines.append(AUTO_START_MARKER)
        new_lines.extend(auto_lines)
        new_lines.append(AUTO_END_MARKER)

    write_lines("template.m3u", new_lines)
    print("✅ Live events (Cricket & Football) auto-section আপডেট হয়েছে।")

# =============== STEP 4: Final output with greeting ===============

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
    # যেসব চ্যানেল Toffee সোর্স থেকে রিফ্রেশ হবে
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
        "Discovery",
    ]

    safe_run("Toffee Channel Refresh", lambda: update_channels(channel_list))
    safe_run("Xtream BDIX/CDN Normal Sync", sync_xtream_bdix_cdn_into_template)
    safe_run("Live Events Sync", sync_live_events_into_template)
    safe_run("Final Output", generate_final_file)