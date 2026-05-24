import os
import re
import requests
import urllib.parse
import html
import time
from datetime import datetime, timedelta

try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None


HTTP_TIMEOUT = 20

TOFFEE_SOURCE_URL = "https://raw.githubusercontent.com/BINOD-XD/Toffee-Auto-Update-Playlist/refs/heads/main/toffee_OTT_Navigator.m3u"

XTV_USERNAME = "shanto4455"
XTV_PASSWORD = "01974264455"
XTV_DOMAIN = "http://tv.dgtv.xyz:8080"

XTV_URL_STREAMS = f"{XTV_DOMAIN}/player_api.php?username={XTV_USERNAME}&password={XTV_PASSWORD}&action=get_live_streams"
XTV_URL_CATEGORIES = f"{XTV_DOMAIN}/player_api.php?username={XTV_USERNAME}&password={XTV_PASSWORD}&action=get_live_categories"

AUTO_START_MARKER = "#EXTM3U-LIVE-AUTO-START"
AUTO_END_MARKER = "#EXTM3U-LIVE-AUTO-END"

LOCAL_XTV_USERNAME = "24212366"
LOCAL_XTV_PASSWORD = "66236233"
LOCAL_XTV_DOMAIN = "http://172.21.22.23:8080"
LOCAL_XTV_URL_STREAMS = f"{LOCAL_XTV_DOMAIN}/player_api.php"

LOCAL_AUTO_START_MARKER = "#EXTM3U-LOCAL-XTREAM-AUTO-START"
LOCAL_AUTO_END_MARKER = "#EXTM3U-LOCAL-XTREAM-AUTO-END"


TOFFEE_PROTECTED_CHANNELS = {
    "CARTOON NETWORK",
    "POGO",
    "DISCOVERY KIDS",
    "CARTOON NETWORK HD",
    "CARTOON NETWORK SD",
    "TLC HD",
    "SONY BBC EARTH HD VIP",
    "SONY BBC EARTH HD",
    "DISCOVERY",
}


category_map = {
    "BTV NATIONAL HD": "Bangladeshi Channel",
    "BTV NEWS HD": "News Channel",
    "BTV CHATTAGRAM": "Bangladeshi Channel",
    "ATN BANGLA HD": "Bangladeshi Channel",
    "CHANNEL I HD": "Bangladeshi Channel",
    "EKUSHEY TV HD": "Bangladeshi Channel",
    "NTV": "Bangladeshi Channel",
    "RTV HD": "Bangladeshi Channel",
    "ATN NEWS": "News Channel",
    "SOMOY TV HD": "News Channel",
    "JAMUNA TV": "News Channel",
    "INDEPENDENT TV": "News Channel",
    "CHANNEL 24 HD": "News Channel",
    "DBC NEWS HD": "News Channel",
    "NEWS24 HD": "News Channel",
    "EKATTOR TV HD": "News Channel",
    "EKHON TV HD": "Bangladeshi Channel",
    "SATV HD": "Bangladeshi Channel",
    "BANGLA VISION": "Bangladeshi Channel",
    "DESH TV": "Bangladeshi Channel",
    "MYTV HD": "Bangladeshi Channel",
    "BOISHAKHI TV HD": "Bangladeshi Channel",
    "GAZI TV HD": "Bangladeshi Channel",
    "ASIAN TV HD": "Bangladeshi Channel",
    "DEEPTO TV HD": "Bangladeshi Channel",
    "MAASRANGA TV HD": "Bangladeshi Channel",
    "MOHONA TV HD": "Bangladeshi Channel",
    "BANGLA TV HD": "Bangladeshi Channel",
    "NAGORIK TV HD": "Bangladeshi Channel",
    "DURONTO TV HD": "Bangladeshi Channel",
    "ANANDA TV": "Bangladeshi Channel",
    "CHANNEL 9 HD": "Bangladeshi Channel",

    "STAR JOLSHA HD": "Indian Popular",
    "ZEE BANGLA HD": "Indian Popular",
    "COLORS BANGLA HD": "Indian Popular",
    "SUN BANGLA HD": "Indian Popular",
    "JALSHA MOVIES HD": "Indian Popular",
    "SONY ATTH": "Indian Popular",
    "ZEE BANGLA SONAR": "Indian Popular",
    "ENTER 10 BANGLA": "Indian Popular",
    "KHUSHBOO": "Indian Popular",
    "AKASH BANGLA": "Indian Popular",
    "STAR PLUS HD": "Indian Popular",

    "SONY HD": "Hindi Channel",
    "ZEE TV HD": "Hindi Channel",
    "COLORS HD": "Hindi Channel",
    "SUB TV HD": "Hindi Channel",
    "STAR BHARAT HD": "Hindi Channel",
    "&TV HD": "Hindi Channel",
    "ARY DIGITAL HD": "Hindi Channel",
    "HUM TV HD": "Hindi Channel",

    "STAR GOLD HD": "Hindi Movie",
    "ZEE CINEMA HD": "Hindi Movie",
    "& PICTURE HD": "Hindi Movie",
    "SONY MAX HD": "Hindi Movie",
    "COLORS CINEPLEX HD": "Hindi Movie",
    "STAR GOLD 2 HD": "Hindi Movie",
    "STAR GOLD SEL HD": "Hindi Movie",
    "B4U MOVIES": "Hindi Movie",

    "T SPORTS HD": "Sports",
    "T SPORTS FUL HD": "Sports",
    "SONY TEN 1 HD": "Sports",
    "SONY TEN 2 HD": "Sports",
    "SONY TEN 3 HD": "Sports",
    "SONY TEN 5 HD": "Sports",
    "STAR SPORTS 1 HD": "Sports",
    "STAR SPORTS 2 HD": "Sports",
    "STAR SPORTS HINDI 2 HD": "Sports",
    "STAR SPORTS SL1 HD": "Sports",
    "STAR SPORTS SL2 HD": "Sports",
    "STAR SPORTS 3": "Sports",
    "EUROSPORTS HD": "Sports",
    "PTV SPORTS HD": "Sports",
    "A SPORTS HD": "Sports",
    "GEO SUPER SPORTS": "Sports",
    "TNT SPORTS 1 HD": "Sports",
    "TNT SPORTS 2 HD": "Sports",
    "TNT SPORTS 3 HD": "Sports",
    "TNT SPORTS 4 HD": "Sports",
    "LOTUS": "Sports",
    "SUPER SPORTS LIVE HD": "Sports",
    "BEIN SPORTS 1 HD ENG": "Sports",
    "BEIN  SPORTS 2 HD ENG": "Sports",
    "BEIN SPORTS HD USA": "Sports",
    "SKY PREMIER LEAGUE HD": "Sports",
    "SKY SPORTS GOLF HD": "Sports",
    "NBC GOLF HD": "Sports",
    "FOX SPORTS 501 HD": "Sports",
    "WILLOW CRICKET HD": "Sports",
    "WILLOW CRICKET XTRA HD": "Sports",
    "SKY SPORTS CRICKET HD": "Sports",
    "SUPER CRICKET HD": "Sports",
    "TEN SPORTS HD": "Sports",
    "SATAR SPORTS HINDI 1 HD": "Sports",

    "24 GANTHA NEWS": "News Channel",
    "R.BANGLA NEWS": "News Channel",
    "ZEE NEWS": "News Channel",
    "ABP NEWS": "News Channel",
    "AAJ TAK HD": "News Channel",
    "GEO NEWS": "News Channel",
    "ARY NEWS ASIA": "News Channel",
    "SAMAA NEWS": "News Channel",
    "AL JAZEERA NEWS": "News Channel",
    "BBC WORLD": "News Channel",
    "CNN INTERNATIONAL": "News Channel",
    "CGTN NEWS": "News Channel",
    "DW NEWS ENG": "News Channel",
    "NDTV 24/7": "News Channel",
    "NDTV INDIA": "News Channel",

    "DISCOVERY HD": "Infotainment",
    "NAT GEO HD": "Infotainment",
    "NAT GEO WILD HD": "Infotainment",
    "ANIMAL PLANET HD": "Infotainment",
    "SONY BBC EARTH HD": "Infotainment",
    "TRAVEL  XP HD": "Infotainment",
    "HISTORY TV18 HD": "Infotainment",
    "TLC HD": "Infotainment",
    "DISCOVERY SCIENCE": "Infotainment",

    "CARTOON NETWORK HD": "Kids",
    "NICK TV HD+": "Kids",
    "DISNEY INT. HD": "Kids",
    "CARTOON NETWORK SD": "Kids",
    "NICK SD": "Kids",
    "SONIC": "Kids",
    "POGO": "Kids",
    "NICKJUNIOR": "Kids",
    "HANGAMA SD": "Kids",
    "DISCOVERY KIDS": "Kids",
    "DISNEY CHANNELS": "Kids",
    "DUSENY JUNIOR": "Kids",

    "SONY PIX HD": "English Movie",
    "& FLIX HD": "English Movie",
    "AXN HD": "English Movie",
    "COLORS INFINITY HD": "English Movie",
    "STAR MOVIES HD": "English Movie",
    "STAR MOVIES SEL HD": "English Movie",
    "MN+ HD": "English Movie",
    "MOVIES NOW HD": "English Movie",
    "ZEE CAFE HD": "English Movie",
    "& PRIVE HD": "English Movie",
    "HBO HD": "English Movie",
    "HBO HITS HD": "English Movie",
    "ROMEDY NOW": "English Movie",
    "MNX": "English Movie",

    "B4U MUSIC": "Music",
    "SANGEET BANGLA": "Music",
    "9XM": "Music",
    "MASTIII": "Music",
    "MTV INDIA HD": "Music",

    "PEACE TV BANGLA HD": "Islamic",
    "SAUDI QURAN": "Islamic",
    "SAUDI SUNNAH": "Islamic",
}


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

            yield start, i, extinf, headers, url
        else:
            i += 1


def get_name_from_extinf(extinf_line):
    m = re.search(r",\s*(.+?)\s*$", extinf_line.strip())
    return m.group(1).strip() if m else ""


# এটা শুধু Toffee protected/filter এর জন্য রাখা হয়েছে
def clean_channel_name(name):
    if not name:
        return ""

    name = str(name).upper()

    replacements = {
        "FULL HD": "HD",
        "FUL HD": "HD",
        "FHD": "HD",
        "HD+": "HD",
        " UHD ": " HD ",
    }

    for old, new in replacements.items():
        name = name.replace(old, new)

    name = re.sub(r"[^A-Z0-9&+\- ]", "", name)
    name = re.sub(r"\s+", " ", name)

    return name.strip()


def is_toffee_protected(name):
    clean_protected = {clean_channel_name(x) for x in TOFFEE_PROTECTED_CHANNELS}
    return clean_channel_name(name) in clean_protected


def detect_category(name):
    n = str(name).upper()

    if any(x in n for x in ["SPORT", "CRICKET", "WILLOW", "BEIN", "TNT", "GOLF", "ESPN", "TEN"]):
        return "Sports"
    if any(x in n for x in ["NEWS", "CNN", "BBC", "AL JAZEERA", "NDTV", "AAJ TAK", "DW", "CGTN"]):
        return "News Channel"
    if any(x in n for x in ["MOVIE", "MOVIES", "CINEMA", "PIX", "HBO", "MAX", "FLIX", "MNX", "PRIVE", "GOLD"]):
        return "Movie"
    if any(x in n for x in ["MUSIC", "MTV", "9XM", "MASTI", "SANGEET"]):
        return "Music"
    if any(x in n for x in ["KIDS", "CARTOON", "POGO", "SONIC", "NICK", "DISNEY", "HANGAMA"]):
        return "Kids"
    if any(x in n for x in ["QURAN", "SUNNAH", "ISLAMIC", "PEACE TV"]):
        return "Islamic"
    if any(x in n for x in ["DISCOVERY", "NAT GEO", "ANIMAL PLANET", "HISTORY", "TLC", "TRAVEL"]):
        return "Infotainment"
    if any(x in n for x in ["BANGLA", "BTV", "NTV", "RTV", "ATN", "DESH", "GAZI", "EKUSHEY", "CHANNEL I"]):
        return "Bangladeshi Channel"

    return "Unknown"


def get_category(name):
    key = str(name).strip().upper()
    return category_map.get(key, detect_category(name))


logo_cache = {}


def get_logo_from_google(channel_name):
    if channel_name in logo_cache:
        return logo_cache[channel_name]

    try:
        clean_name = (
            channel_name
            .replace("FUL HD", "")
            .replace("FULL HD", "")
            .replace("HD+", "")
            .replace("HD", "")
            .replace("SD", "")
            .strip()
        )

        query = urllib.parse.quote(clean_name + " tv channel logo png")
        google_url = f"https://www.google.com/search?tbm=isch&q={query}"

        google_headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 15) AppleWebKit/537.36 Chrome/120 Mobile Safari/537.36"
        }

        r = requests.get(google_url, headers=google_headers, timeout=15)
        text = html.unescape(r.text)

        image_links = re.findall(
            r'https://[^"\']+\.(?:png|jpg|jpeg|webp)',
            text
        )

        for img in image_links:
            low = img.lower()
            if (
                "google" not in low
                and "gstatic" not in low
                and "encrypted-tbn" not in low
                and "logo" in low
            ):
                logo_cache[channel_name] = img
                return img

        for img in image_links:
            low = img.lower()
            if (
                "google" not in low
                and "gstatic" not in low
                and "encrypted-tbn" not in low
            ):
                logo_cache[channel_name] = img
                return img

    except Exception:
        pass

    logo_cache[channel_name] = ""
    return ""


def inject_auto_section(marker_start, marker_end, auto_lines):
    lines = read_lines("template.m3u")
    new_lines = []
    i = 0
    n = len(lines)

    found_start = False
    found_end = False

    while i < n:
        line = lines[i]

        if line.strip() == marker_start:
            found_start = True
            new_lines.append(marker_start)

            i += 1
            while i < n and lines[i].strip() != marker_end:
                i += 1

            new_lines.extend(auto_lines)

            if i < n and lines[i].strip() == marker_end:
                found_end = True
                new_lines.append(marker_end)
                i += 1

            continue

        new_lines.append(line)
        i += 1

    if not found_start or not found_end:
        if new_lines and new_lines[-1].strip() != "":
            new_lines.append("")
        new_lines.append(marker_start)
        new_lines.extend(auto_lines)
        new_lines.append(marker_end)

    write_lines("template.m3u", new_lines)


def update_channels(channel_names):
    if not os.path.exists("template.m3u"):
        raise FileNotFoundError("template.m3u not found")

    r = requests.get(TOFFEE_SOURCE_URL, timeout=HTTP_TIMEOUT)
    r.raise_for_status()
    source_data = r.text.splitlines()

    lines = read_lines("template.m3u")
    lower_targets = [clean_channel_name(c) for c in channel_names]

    src_map = {}

    for _, __, extinf, headers, url in iter_blocks(source_data):
        name = get_name_from_extinf(extinf).strip()
        if name:
            src_map[clean_channel_name(name)] = (headers, url)

    out = []
    i, n = 0, len(lines)

    while i < n:
        if lines[i].startswith("#EXTINF:"):
            block = next(iter_blocks(lines[i:]), None)

            if block:
                b_start, b_end, extinf, old_headers, old_url = block
                b_end += i

                name = clean_channel_name(get_name_from_extinf(extinf))

                if name in lower_targets and name in src_map:
                    new_headers, new_url = src_map[name]

                    out.append(extinf)
                    out.extend(new_headers)

                    if new_url:
                        out.append(new_url)

                    i = b_end
                    continue

                out.extend(lines[i:b_end])
                i = b_end
                continue

        out.append(lines[i])
        i += 1

    write_lines("template.m3u", out)
    print("✅ Toffee channel refresh complete")


def sync_live_events_into_template():
    if not os.path.exists("template.m3u"):
        raise FileNotFoundError("template.m3u not found")

    headers_req = {
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 9; Redmi S2 Build/PKQ1.180904.001)",
        "Accept": "*/*",
        "Connection": "Keep-Alive",
        "Accept-Encoding": "gzip",
        "X-Requested-With": "com.ottplay.ottplay"
    }

    streams = requests.get(XTV_URL_STREAMS, headers=headers_req, timeout=HTTP_TIMEOUT).json()
    categories = requests.get(XTV_URL_CATEGORIES, headers=headers_req, timeout=HTTP_TIMEOUT).json()

    category_id_map = {
        str(c.get("category_id")): c.get("category_name", "")
        for c in categories
    }

    target_categories = {
        "cricket live event",
        "football live event"
    }

    auto_lines = []

    for ch in streams:
        name = ch.get("name", "").strip()
        stream_id = ch.get("stream_id")
        logo = ch.get("stream_icon", "") or ""
        category_id = str(ch.get("category_id", "")).strip()

        if not name or not stream_id:
            continue

        if is_toffee_protected(name):
            continue

        category_name = category_id_map.get(category_id, "").strip()

        if category_name.lower() not in target_categories:
            continue

        stream_url = f"{XTV_DOMAIN}/live/{XTV_USERNAME}/{XTV_PASSWORD}/{stream_id}.m3u8"

        auto_lines.append(
            f'#EXTINF:-1 tvg-logo="{logo}" group-title="{category_name}",{name}'
        )
        auto_lines.append(stream_url)
        auto_lines.append("")

    inject_auto_section(
    AUTO_START_MARKER,
    AUTO_END_MARKER,
    auto_lines
)

print("✅ Cricket & Football live events updated")