#!/usr/bin/env python3
"""
Healthcare Updates India - News Fetcher
Fetches healthcare news from RSS feeds, PIB, MCI/NMC, Telangana health dept.
"""

import json
import os
import re
import hashlib
from datetime import datetime, timedelta
from pathlib import Path

try:
    import feedparser
except ImportError:
    print("Installing feedparser...")
    os.system("pip install feedparser")
    import feedparser

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("Installing requests and beautifulsoup4...")
    os.system("pip install requests beautifulsoup4")
    import requests
    from bs4 import BeautifulSoup

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

TODAY = datetime.now().strftime("%Y-%m-%d")
YESTERDAY = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

# ============================================================
# RSS FEEDS - Healthcare Sources
# ============================================================

RSS_FEEDS = {
    # Central Government
    "pib_health": {
        "url": "https://pib.gov.in/RssMain.aspx?ModId=6&Lang=1&Regid=3",
        "category": "central",
        "tag": "central",
        "tag_label": "Central Govt",
        "keywords": ["health", "medical", "hospital", "aiims", "nmc", "mci", "pharma", "ayushman", "cowin", "vaccine", "doctor", "nursing"],
    },
    "pib_english": {
        "url": "https://pib.gov.in/RssMain.aspx?ModId=6&Lang=1&Regid=1",
        "category": "central",
        "tag": "central",
        "tag_label": "Central Govt",
        "keywords": ["health", "medical", "hospital", "nmc", "mci", "pharma", "ayushman", "doctor", "nursing"],
    },
    # MCI/NMC
    "nmc_announcements": {
        "url": "https://www.nmc.org.in/announcement/feed/",
        "category": "mci",
        "tag": "mci",
        "tag_label": "NMC",
        "keywords": [],
    },
    # Medical News India
    "medical_dialogues": {
        "url": "https://www.medicaldialogues.in/feed/",
        "category": "hospitals",
        "tag": "hospital",
        "tag_label": "Hospital",
        "keywords": ["telangana", "hyderabad", "mci", "nmc", "medical college", "hospital"],
    },
    "times_health": {
        "url": "https://timesofindia.indiatimes.com/rssfeeds/1898055.cms",
        "category": "central",
        "tag": "central",
        "tag_label": "National",
        "keywords": ["health", "medical", "hospital", "doctor", "pharma", "covid", "vaccine"],
    },
    "ndtv_health": {
        "url": "https://feeds.feedburner.com/ndtvnews-health",
        "category": "central",
        "tag": "central",
        "tag_label": "National",
        "keywords": [],
    },
    "the_hindu_health": {
        "url": "https://www.thehindu.com/feeder/default.rss",
        "category": "central",
        "tag": "central",
        "tag_label": "National",
        "keywords": ["health", "medical", "hospital", "nmc", "mci", "pharma"],
    },
}

# Telangana-specific sources
TELANGANA_FEEDS = {
    "telangana_today": {
        "url": "https://www.telanganaToday.com/feed/",
        "category": "telangana",
        "tag": "telangana",
        "tag_label": "Telangana",
        "keywords": ["health", "hospital", "medical", "knruhs", "dmhs", "kaloji", "doctor", "nursing"],
    },
    "telangana_heatth": {
        "url": "https://www.telangana.gov.in/feed/",
        "category": "telangana",
        "tag": "telangana",
        "tag_label": "Telangana",
        "keywords": ["health", "hospital", "medical"],
    },
}

# ============================================================
# KEYWORD CATEGORIES for auto-classification
# ============================================================

RULES_KEYWORDS = [
    "regulation", "rule", "amendment", "notification", "circular",
    "guideline", "order", "act", "policy", "compliance", "mandatory",
    "revised", "updated", "new rule", "guidelines issued",
]

MCI_KEYWORDS = [
    "mci", "nmc", "national medical commission", "medical council",
    "nbe", "neet", "medical education", "pg medical", "mbbs",
    "medical college recognition", "inspection", "accreditation",
]

TELANGANA_KEYWORDS = [
    "telangana", "hyderabad", "knruhs", "kaloji", "dmhs",
    "telangana health", "tsmssc", "osmania medical", "gandhi medical",
    "kamineni", "apollo hyderabad", "yashoda", "star hospital",
    "telangana government hospital", "108 ambulance", "kcr kits",
    "aarogyasri", "telangana medical",
]

# Google News RSS - more reliable than direct RSS feeds
GOOGLE_NEWS_RSS = {
    "mci_nmc_news": "https://news.google.com/rss/search?q=MCI+NMC+medical+council+india+2026&hl=en-IN&gl=IN&ceid=IN:en",
    "telangana_health": "https://news.google.com/rss/search?q=telangana+health+hospital+medical+2026&hl=en-IN&gl=IN&ceid=IN:en",
    "india_health_news": "https://news.google.com/rss/search?q=india+healthcare+hospital+medical+council+regulation+2026&hl=en-IN&gl=IN&ceid=IN:en",
    "india_medical_regulation": "https://news.google.com/rss/search?q=india+medical+college+regulation+rule+circular+2026&hl=en-IN&gl=IN&ceid=IN:en",
    "telangana_medical_college": "https://news.google.com/rss/search?q=telangana+medical+college+KNRUHS+admission+2026&hl=en-IN&gl=IN&ceid=IN:en",
    "hospital_india": "https://news.google.com/rss/search?q=new+hospital+india+launch+2026&hl=en-IN&gl=IN&ceid=IN:en",
    "ayushman_bharat": "https://news.google.com/rss/search?q=ayushman+bharat+scheme+india+health+2026&hl=en-IN&gl=IN&ceid=IN:en",
}

HOSPITAL_KEYWORDS = [
    "hospital", "medical college", "aiims", "clinic", "healthcare center",
    "nursing home", "diagnostic center", "super specialty",
]

LAUNCH_KEYWORDS = [
    "launch", "inaugurate", "new scheme", "new program", "initiative",
    "rollout", "introduce", "announce new", "flag off", "commission",
]


def make_id(title, source):
    """Create unique ID for a news item."""
    text = f"{title}_{source}".lower().strip()
    return hashlib.md5(text.encode()).hexdigest()[:12]


def classify_item(title, description, source_key):
    """Auto-classify a news item into categories."""
    text = f"{title} {description}".lower()

    # Check Telangana
    if any(kw in text for kw in TELANGANA_KEYWORDS):
        return "telangana", "telangana", "Telangana"

    # Check MCI/NMC
    if any(kw in text for kw in MCI_KEYWORDS):
        return "mci", "mci", "NMC"

    # Check rules/regulations
    if any(kw in text for kw in RULES_KEYWORDS):
        return "regulations", "regulation", "Regulation"

    # Check launches
    if any(kw in text for kw in LAUNCH_KEYWORDS):
        return "launches", "launch", "Launch"

    # Check hospitals
    if any(kw in text for kw in HOSPITAL_KEYWORDS):
        return "hospitals", "hospital", "Hospital"

    return "central", "central", "National"


def is_healthcare_related(title, description, keywords):
    """Check if an item is healthcare-related."""
    if not keywords:
        return True  # If no filter keywords, include all
    text = f"{title} {description}".lower()
    return any(kw.lower() in text for kw in keywords)


def fetch_rss(feed_key, feed_config):
    """Fetch and parse an RSS feed."""
    items = []
    url = feed_config["url"]
    category = feed_config["category"]
    keywords = feed_config.get("keywords", [])

    try:
        print(f"  Fetching: {feed_key} ({url[:60]}...)")
        feed = feedparser.parse(url)

        for entry in feed.entries[:20]:
            title = entry.get("title", "").strip()
            description = entry.get("summary", entry.get("description", "")).strip()
            link = entry.get("link", "")
            published = entry.get("published", entry.get("updated", ""))

            # Clean HTML from description
            if description:
                description = BeautifulSoup(description, "html.parser").get_text()[:300]

            # Check if healthcare-related
            if not is_healthcare_related(title, description, keywords):
                continue

            # Classify
            cat, tag, tag_label = classify_item(title, description, feed_key)

            items.append({
                "id": make_id(title, feed_key),
                "title": title,
                "description": description,
                "url": link,
                "source": feed_key.replace("_", " ").title(),
                "date": published[:10] if published else TODAY,
                "category": cat,
                "tag": tag,
                "tag_label": tag_label,
                "priority": "high" if any(kw in title.lower() for kw in ["breaking", "urgent", "circular", "notification", "new rule"]) else "medium",
            })

        print(f"    Found {len(items)} relevant items")
    except Exception as e:
        print(f"    Error: {e}")

    return items


def fetch_pib_health():
    """Fetch health-related press releases from PIB."""
    items = []
    try:
        # PIB health ministry releases
        url = "https://pib.gov.in/allRel.aspx"
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            for link in soup.select("a[href*='PressRelease']")[:15]:
                title = link.get_text(strip=True)
                if any(kw in title.lower() for kw in ["health", "medical", "hospital", "nmc", "mci", "doctor", "pharma"]):
                    items.append({
                        "id": make_id(title, "pib"),
                        "title": title,
                        "description": f"PIB Press Release: {title}",
                        "url": f"https://pib.gov.in{link.get('href', '')}",
                        "source": "PIB India",
                        "date": TODAY,
                        "category": "central",
                        "tag": "central",
                        "tag_label": "Central Govt",
                        "priority": "high",
                    })
    except Exception as e:
        print(f"  PIB fetch error: {e}")
    return items


def fetch_telangana_health():
    """Fetch Telangana-specific health news."""
    items = []

    # Try Telangana government health department
    try:
        url = "https://hmwssb.telangana.gov.in/"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            for link in soup.select("a")[:20]:
                text = link.get_text(strip=True)
                if len(text) > 15 and any(kw in text.lower() for kw in ["health", "hospital", "scheme", "notification", "circular"]):
                    items.append({
                        "id": make_id(text, "ts_health"),
                        "title": text[:150],
                        "description": f"Telangana Health Department: {text}",
                        "url": link.get("href", url),
                        "source": "Telangana Health Dept",
                        "date": TODAY,
                        "category": "telangana",
                        "tag": "telangana",
                        "tag_label": "Telangana",
                        "priority": "medium",
                    })
    except Exception as e:
        print(f"  Telangana health dept error: {e}")

    # KNRUHS
    try:
        url = "https://knruhs.telangana.gov.in/"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            for link in soup.select("a")[:15]:
                text = link.get_text(strip=True)
                if len(text) > 15 and any(kw in text.lower() for kw in ["notification", "circular", "counseling", "admission", "mbbs", "bds", "nursing"]):
                    items.append({
                        "id": make_id(text, "knruhs"),
                        "title": text[:150],
                        "description": f"KNRUHS Update: {text}",
                        "url": link.get("href", url),
                        "source": "KNRUHS Telangana",
                        "date": TODAY,
                        "category": "telangana",
                        "tag": "telangana",
                        "tag_label": "KNRUHS",
                        "priority": "high",
                    })
    except Exception as e:
        print(f"  KNRUHS error: {e}")

    return items


def add_static_telangana_data():
    """Add important static Telangana healthcare information."""
    return [
        {
            "id": "ts_scheme_ayushman",
            "title": "Ayushman Bharat - Pradhan Mantri Jan Arogya Yojana (PMJAY) in Telangana",
            "description": "Provides health insurance cover of Rs 5 lakh per family per year for secondary and tertiary care hospitalization to over 12 crore poor and vulnerable families.",
            "url": "https://www.pmjay.gov.in/",
            "source": "MoHFW India",
            "date": TODAY,
            "category": "telangana",
            "tag": "telangana",
            "tag_label": "Schemes",
            "priority": "medium",
            "subcategory": "schemes",
        },
        {
            "id": "ts_scheme_kcr_kits",
            "title": "KCR Kits Scheme - Telangana Maternal & Child Welfare",
            "description": "Provides nutrition kit and cash incentive to pregnant women and newborns. Covers institutional delivery, post-natal care, and immunization.",
            "url": "https://hmwssb.telangana.gov.in/",
            "source": "Telangana Health Dept",
            "date": TODAY,
            "category": "telangana",
            "tag": "telangana",
            "tag_label": "Schemes",
            "priority": "medium",
            "subcategory": "schemes",
        },
        {
            "id": "ts_knruhs_counseling",
            "title": "KNRUHS MBBS/BDS Counseling 2026 - Web-based Counseling for Medical Admissions",
            "description": "Kaloji Narayana Rao University of Health Sciences conducts web-based counseling for MBBS, BDS, BAMS, BHMS, BSc Nursing admissions in Telangana state medical colleges.",
            "url": "https://knruhs.telangana.gov.in/",
            "source": "KNRUHS",
            "date": TODAY,
            "category": "telangana",
            "tag": "telangana",
            "tag_label": "KNRUHS",
            "priority": "high",
            "subcategory": "knruhs",
        },
        {
            "id": "ts_dmhs_circular",
            "title": "DM&HS Telangana - Director of Medical Education Updates",
            "description": "Directorate of Medical & Health Services, Telangana oversees government medical colleges, hospitals, and public health institutions across the state.",
            "url": "https://dme.telangana.gov.in/",
            "source": "DM&HS Telangana",
            "date": TODAY,
            "category": "telangana",
            "tag": "telangana",
            "tag_label": "DM&HS",
            "priority": "medium",
            "subcategory": "dmhs",
        },
        {
            "id": "ts_kaloji_university",
            "title": "Kaloji Narayana Rao University of Health Sciences - Academic Updates",
            "description": "Health sciences university in Telangana offering courses in Medicine, Dentistry, Pharmacy, Nursing, and Allied Health Sciences.",
            "url": "https://knruhs.telangana.gov.in/",
            "source": "KNRUHS Telangana",
            "date": TODAY,
            "category": "telangana",
            "tag": "telangana",
            "tag_label": "Kaloji Univ",
            "priority": "medium",
            "subcategory": "kaloji",
        },
        {
            "id": "ts_108_ambulance",
            "title": "108 Emergency Ambulance Service - Telangana",
            "description": "Free emergency ambulance service across Telangana. Over 1,000 ambulances operating 24/7. Dial 108 for emergency medical transport.",
            "url": "https://108.telangana.gov.in/",
            "source": "Telangana EMS",
            "date": TODAY,
            "category": "telangana",
            "tag": "telangana",
            "tag_label": "Telangana",
            "priority": "low",
            "subcategory": "hospitals",
        },
        {
            "id": "ts_gandhi_hospital",
            "title": "Gandhi Hospital Secunderabad - Major Government Hospital Updates",
            "description": "One of the oldest and largest government hospitals in Telangana. 1,500+ beds, serves thousands daily. Updates on OPD, IPD, emergency services.",
            "url": "https://dme.telangana.gov.in/",
            "source": "Gandhi Hospital",
            "date": TODAY,
            "category": "telangana",
            "tag": "telangana",
            "tag_label": "Hospitals",
            "priority": "medium",
            "subcategory": "hospitals",
        },
        {
            "id": "ts_osmania_hospital",
            "title": "Osmania General Hospital - Heritage Hospital Updates",
            "description": "Historic government hospital in Hyderabad, established 1910. Major trauma center and teaching hospital attached to Osmania Medical College.",
            "url": "https://dme.telangana.gov.in/",
            "source": "Osmania Hospital",
            "date": TODAY,
            "category": "telangana",
            "tag": "telangana",
            "tag_label": "Hospitals",
            "priority": "medium",
            "subcategory": "hospitals",
        },
    ]


def add_static_mci_data():
    """Add important static MCI/NMC information."""
    return [
        {
            "id": "nmc_overview",
            "title": "National Medical Commission (NMC) - Replaced MCI in 2020",
            "description": "NMC is the regulatory body for medical education and practice in India. Replaced the Medical Council of India through the NMC Act, 2019. Key functions: medical education regulation, doctor registration, ethical standards.",
            "url": "https://www.nmc.org.in/",
            "source": "NMC India",
            "date": TODAY,
            "category": "mci",
            "tag": "mci",
            "tag_label": "NMC",
            "priority": "medium",
        },
        {
            "id": "nmc_registration",
            "title": "NMC Doctor Registration - Online Registration Portal",
            "description": "All medical practitioners must register with NMC. Online registration available at nmc.org.in. Includes primary registration, additional qualification, and state medical council registration.",
            "url": "https://www.nmc.org.in/",
            "source": "NMC India",
            "date": TODAY,
            "category": "mci",
            "tag": "mci",
            "tag_label": "NMC",
            "priority": "medium",
        },
        {
            "id": "nmc_ethics",
            "title": "NMC Ethics Committee - Professional Standards & Medical Ethics",
            "description": "NMC Ethics Committee handles complaints against medical practitioners, sets ethical standards for medical profession in India.",
            "url": "https://www.nmc.org.in/",
            "source": "NMC India",
            "date": TODAY,
            "category": "mci",
            "tag": "mci",
            "tag_label": "NMC",
            "priority": "low",
        },
        {
            "id": "mci_old_regulations",
            "title": "MCI Legacy - Graduate Medical Education Regulations",
            "description": "Previous MCI regulations still partially in effect. Covers MBBS curriculum, PG medical education standards, medical college recognition requirements.",
            "url": "https://www.mciindia.org/",
            "source": "MCI Portal",
            "date": TODAY,
            "category": "mci",
            "tag": "mci",
            "tag_label": "MCI",
            "priority": "low",
        },
    ]


def add_static_regulations_data():
    """Add important static regulations information."""
    return [
        {
            "id": "reg_clinical_establishments",
            "title": "Clinical Establishments (Registration & Regulation) Act, 2010",
            "description": "Mandatory registration of all clinical establishments. Standards for infrastructure, staffing, and patient care. Applicable across India including Telangana.",
            "url": "https://clinical establishments.gov.in/",
            "source": "MoHFW India",
            "date": TODAY,
            "category": "regulations",
            "tag": "regulation",
            "tag_label": "Regulation",
            "priority": "medium",
        },
        {
            "id": "reg_pharma_act",
            "title": "Drugs and Cosmetics Act, 1940 - Recent Amendments",
            "description": "Governs import, manufacture, distribution, and sale of drugs and cosmetics in India. Regular amendments for new drug approvals and safety.",
            "url": "https://cdsco.gov.in/",
            "source": "CDSCO India",
            "date": TODAY,
            "category": "regulations",
            "tag": "regulation",
            "tag_label": "Regulation",
            "priority": "low",
        },
        {
            "id": "reg_mbp_act",
            "title": "Medical Termination of Pregnancy (Amendment) Act, 2021",
            "description": "Expanded access to safe abortion services. Increased gestation limit from 20 to 24 weeks for special categories. Made provision for medical termination.",
            "url": "https://www.nmc.org.in/",
            "source": "NMC India",
            "date": TODAY,
            "category": "regulations",
            "tag": "regulation",
            "tag_label": "Regulation",
            "priority": "medium",
        },
        {
            "id": "reg_ndps",
            "title": "Narcotic Drugs and Psychotropic Substances Act, 1985",
            "description": "Regulates controlled substances. Important for hospitals and pharmacies handling narcotic drugs for medical purposes.",
            "url": "https://www.narcoticsindia.nic.in/",
            "source": "Govt of India",
            "date": TODAY,
            "category": "regulations",
            "tag": "regulation",
            "tag_label": "Regulation",
            "priority": "low",
        },
    ]


def merge_and_deduplicate(existing, new_items):
    """Merge new items with existing, deduplicate by ID."""
    seen = set()
    merged = []

    # Keep existing items
    for item in existing:
        if item["id"] not in seen:
            seen.add(item["id"])
            merged.append(item)

    # Add new items
    for item in new_items:
        if item["id"] not in seen:
            seen.add(item["id"])
            merged.append(item)

    return merged


def save_json(filename, data):
    """Save data to JSON file."""
    filepath = DATA_DIR / filename
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  Saved {len(data)} items to {filename}")


def main():
    print("=" * 60)
    print("HEALTHCARE UPDATES INDIA - News Fetcher")
    print(f"Date: {TODAY}")
    print("=" * 60)

    all_items = {
        "telangana": [],
        "mci": [],
        "regulations": [],
        "hospitals": [],
        "launches": [],
        "central": [],
    }

    # Fetch from RSS feeds
    print("\n[1/4] Fetching RSS feeds...")
    for feed_key, feed_config in RSS_FEEDS.items():
        items = fetch_rss(feed_key, feed_config)
        for item in items:
            cat = item["category"]
            if cat in all_items:
                all_items[cat].append(item)

    # Fetch from Telangana sources
    print("\n[2/4] Fetching Telangana sources...")
    ts_items = fetch_telangana_health()
    all_items["telangana"].extend(ts_items)

    # Fetch from Google News RSS (more reliable)
    print("\n[2.5/4] Fetching Google News RSS...")
    for feed_key, url in GOOGLE_NEWS_RSS.items():
        try:
            print(f"  Fetching: {feed_key}")
            feed = feedparser.parse(url)
            count = 0
            for entry in feed.entries[:10]:
                title = entry.get("title", "").strip()
                link = entry.get("link", "")
                published = entry.get("published", "")
                source_name = entry.get("source", {}).get("title", "Google News")

                if not title:
                    continue

                # Classify
                cat, tag, tag_label = classify_item(title, "", feed_key)

                item = {
                    "id": make_id(title, feed_key),
                    "title": title,
                    "description": f"Source: {source_name}",
                    "url": link,
                    "source": source_name,
                    "date": published[:10] if published else TODAY,
                    "category": cat,
                    "tag": tag,
                    "tag_label": tag_label,
                    "priority": "high" if any(kw in title.lower() for kw in ["breaking", "circular", "notification", "new rule", "mci", "nmc"]) else "medium",
                }
                all_items[cat].append(item)
                count += 1
            print(f"    Found {count} items")
        except Exception as e:
            print(f"    Error: {e}")

    # Fetch PIB
    print("\n[3/4] Fetching PIB health releases...")
    pib_items = fetch_pib_health()
    all_items["central"].extend(pib_items)

    # Add static data
    print("\n[4/4] Adding reference data...")
    all_items["telangana"].extend(add_static_telangana_data())
    all_items["mci"].extend(add_static_mci_data())
    all_items["regulations"].extend(add_static_regulations_data())

    # Save each category
    print("\nSaving data files...")
    for category, items in all_items.items():
        # Load existing data if available
        existing_file = DATA_DIR / f"{category}.json"
        existing = []
        if existing_file.exists():
            try:
                existing = json.loads(existing_file.read_text(encoding="utf-8"))
            except:
                existing = []

        # Merge and deduplicate
        merged = merge_and_deduplicate(existing, items)

        # Sort by priority (high first) then date
        priority_order = {"high": 0, "medium": 1, "low": 2}
        merged.sort(key=lambda x: (priority_order.get(x.get("priority", "low"), 2), x.get("date", "")), reverse=False)
        merged.sort(key=lambda x: priority_order.get(x.get("priority", "low"), 2))

        save_json(f"{category}.json", merged)

    # Summary
    total = sum(len(v) for v in all_items.values())
    print(f"\n{'=' * 60}")
    print(f"DONE! Total items fetched: {total}")
    for cat, items in all_items.items():
        print(f"  {cat}: {len(items)} items")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
