#!/usr/bin/env python3
"""
Green Rabbit Snack Hub — Wholesale Office Snack Delivery Affiliate Site
Site   : https://brightlane.github.io/greenrabbit/
Aff    : https://www.linkconnector.com/ta.php?lc=007949137688006776&atid=greenrabbitsweb
Target : US office managers, HR teams, facilities buyers, breakroom managers
Pages  : ~800+ across EN only (US-only product)
Build  : python3 build.py (~5 seconds)
Deploy : GitHub Actions cron 06:00 UTC daily
"""
import json, re, hashlib, os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from collections import Counter

SITE     = "https://brightlane.github.io/greenrabbit"
NAME     = "Green Rabbit Snack Hub"
AFF      = "https://www.linkconnector.com/ta.php?lc=007949137688006776&atid=greenrabbitsweb"
AFF_HOME = "https://www.warehouse115.com/green-rabbit.html"
NOW      = datetime.now(timezone.utc)
TODAY    = NOW.strftime("%Y-%m-%d")
YEAR     = NOW.year
OG       = SITE + "/og.svg"
OUT      = Path("output")

GOOGLE_V = "eWVDN3vbam9nnaZQu7wAQKyfmJJdM7zjI80l4DGeUrQ"
BING_V   = "574044E39556B8B8DAAF1D1F233C87B0"

def sh(s): return int(hashlib.md5(s.encode()).hexdigest(), 16)
def wc(html): return len(re.findall(r'\b\w+\b', re.sub(r'<[^>]+>',' ', html)))
def read_mins(html):
    words = wc(html)
    return max(4, round(words / (230 if words < 2000 else 450)))

_TITLE_SEEN: dict = {}
def unique_title(title, slug):
    if title not in _TITLE_SEEN:
        _TITLE_SEEN[title] = slug; return title
    tag = slug[-10:].lstrip("-")
    parts = title.rsplit(" | ", 1)
    if len(parts) == 2:
        pipe = f" | {parts[1]}"
        c = (parts[0].rstrip()[:68-len(tag)-3-len(pipe)].rstrip() + f" [{tag}]" + pipe)[:70]
    else:
        c = (title + f" [{tag}]")[:70]
    _TITLE_SEEN[c] = slug; return c

def ttag(kw, sfx="| Green Rabbit Snack Hub"):
    s = f" {sfx}"
    base = kw
    if len(base+s) < 48:
        extras = [" — Complete Guide"," Buying Guide"," — Best Options",
                  " Review & Guide"," — Expert Tips"," for Offices"]
        base += extras[sh(kw) % len(extras)]
    max_b = 64 - len(s)   # cap at 64 to leave room for unique_title dedup suffix
    if len(base) > max_b:
        base = base[:max_b].rsplit(" ",1)[0]
    return base + s


# ── PRODUCT CATEGORIES ────────────────────────────────────────────────────────
CATEGORIES = [
    ("candy",          "Candy & Chocolate",        "bulk office candy chocolate breakroom"),
    ("chips-snacks",   "Chips & Snacks",           "bulk office chips snacks crackers"),
    ("protein-bars",   "Protein & Energy Bars",    "bulk protein bars energy bars office"),
    ("drinks",         "Beverages & Drinks",       "bulk office beverages drinks juice tea"),
    ("nuts-trail-mix", "Nuts & Trail Mix",         "bulk nuts trail mix office snacks"),
    ("cookies-pastries","Cookies & Pastries",      "bulk cookies pastries breakroom"),
    ("fresh-fruit",    "Fresh Fruit",              "bulk fresh fruit office delivery"),
    ("yogurt-dairy",   "Yogurt & Dairy",           "bulk yogurt dairy office delivery"),
    ("healthy-snacks", "Healthy Snacks",           "healthy office snacks bulk delivery"),
    ("holiday-candy",  "Holiday & Seasonal Candy", "bulk holiday candy office"),
]

# ── TOP PRODUCTS (real items from the site) ────────────────────────────────────
PRODUCTS = [
    ("skinny-pop-popcorn","Skinny Pop 100 Calorie Popcorn 0.65oz","$46.72","24-count","chips-snacks","Low-calorie, gluten-free popcorn — a healthy office snack favourite. Each bag is individually portioned for easy grab-and-go. 24 bags per case."),
    ("clif-bar-variety","Clif Bar Energy Bar Variety Pack 2.4oz","$74.70","24-count","protein-bars","Mixed flavours give everyone something they enjoy. 70% organic ingredients. Popular with fitness-conscious office teams. 24 bars per case."),
    ("rxbar-protein","RXBAR Protein Bars Assorted Flavors","$57.93","15-count","protein-bars","Clean-label protein bars with no added sugar. 12g protein per bar. Whole food ingredients listed right on the front of the pack."),
    ("chobani-greek-yogurt","Chobani Greek Yogurt Variety Pack 5.3oz","$61.74","16-count","yogurt-dairy","Individual Greek yogurt cups in assorted flavours. High protein, low sugar options available. Refrigeration required. 16 cups per case."),
    ("blue-diamond-almonds","Blue Diamond Roasted Salted Almonds 1.5oz","$37.32","12-count","nuts-trail-mix","Individual almond snack packs for the breakroom. Heart-healthy, gluten-free. 12 packs per case."),
    ("doritos-nacho","Doritos Nacho Cheese Tortilla Chips 1oz","$56.99","50-count","chips-snacks","The classic office snack. Individually wrapped 1oz bags for easy portion control and minimal mess. 50 bags per case."),
    ("natures-garden-trail","Nature's Garden Healthy Heart Mix 1.2oz","$52.04","42-count","nuts-trail-mix","Non-GMO, gluten-free trail mix. Heart-healthy mix of nuts, dried fruit, and dark chocolate. 42 packs per case."),
    ("arizona-green-tea","Arizona Green Tea with Ginseng and Honey 16oz","$39.58","24-count","drinks","A breakroom favourite. Refreshing iced green tea with ginseng and honey. 24 cans per case."),
    ("ghirardelli-dark","Ghirardelli Intense Dark Chocolate 86% Cacao 4.12oz","$61.17","3-count","candy","Premium dark chocolate for office treat jars and meeting rooms. Rich, sophisticated flavour. 3 bars per case."),
    ("planters-peanuts","Planters Salted Peanuts","$56.80","96-count","nuts-trail-mix","The original office snack. Individual snack packs of salted peanuts. 96 packs per case — great value for large teams."),
    ("werther-caramel","Werther's Original Caramel Hard Candies","$32.16","1-count","candy","Classic caramel candies for the reception desk candy bowl. A crowd-pleaser for visitors and staff alike."),
    ("clif-builders","Clif Builder's 20g Protein Bar Variety Pack","$69.75","18-count","protein-bars","Higher protein option at 20g per bar. Variety pack ensures broad appeal. Great for active office teams. 18 bars per case."),
    ("crystal-light-lemonade","Crystal Light Lemonade Drink Mix","$32.14","16-count","drinks","Low-calorie lemonade drink mix packets. Popular with health-conscious office teams. 16 packets per case."),
    ("lipton-pure-leaf-tea","Lipton Pure Leaf Unsweetened Iced Tea","$52.82","18-count","drinks","Real brewed tea, no artificial flavors, no added sugar. A clean breakroom beverage. 18 bottles per case."),
    ("black-forest-gummy","Black Forest Organic Gummy Bears 0.8oz","$57.30","65-count","candy","Organic gummy bears in individual snack packs. Made with real fruit juice, no artificial colours. 65 packs per case."),
    ("famous-amos-cookies","Famous Amos Chocolate Chip Cookies 2oz","$56.70","36-count","cookies-pastries","Bite-sized chocolate chip cookies in individual packs. A classic office treat. 36 packs per case."),
    ("cloverhill-cinnamon","Cloverhill Big Texas Cinnamon Roll 4oz","$43.53","12-count","cookies-pastries","Individually wrapped bakery-style cinnamon rolls. Perfect for morning meetings and breakfasts. 12 rolls per case."),
    ("fresh-fuji-apples","Fresh Fuji Apples","$39.58","8-count","fresh-fruit","Fresh Fuji apples delivered to your office. Sweet, crisp, and a healthy alternative to packaged snacks. 8 apples per case."),
    ("snapple-variety","Snapple All Natural Juice Drink Variety Pack 20oz","$59.35","24-count","drinks","Popular juice tea drinks in a variety of flavours. All-natural ingredients, no high-fructose corn syrup. 24 bottles per case."),
    ("dove-chocolate","Dove Milk Chocolate Bars 1.44oz","$55.79","18-count","candy","Silky milk chocolate bars for the office candy bowl or meeting room treats. 18 bars per case."),
]

# ── KEYWORD ARCHITECTURE ──────────────────────────────────────────────────────
# General / informational
GENERAL_KW = [
    ("office-snack-delivery",       "Office Snack Delivery",                    "General","40k+"),
    ("bulk-office-snacks",          "Bulk Office Snacks",                       "General","30k+"),
    ("breakroom-snacks",            "Breakroom Snacks",                         "General","30k+"),
    ("office-snack-service",        "Office Snack Service",                     "General","20k+"),
    ("workplace-snacks",            "Workplace Snacks",                         "General","20k+"),
    ("office-snack-delivery-service","Office Snack Delivery Service",           "General","20k+"),
    ("breakroom-food-delivery",     "Breakroom Food Delivery",                  "General","10k+"),
    ("corporate-snack-delivery",    "Corporate Snack Delivery",                 "General","10k+"),
    ("bulk-snacks-for-work",        "Bulk Snacks for Work",                     "General","10k+"),
    ("employee-snacks",             "Employee Snacks",                          "General","20k+"),
    ("office-food-delivery",        "Office Food Delivery",                     "General","20k+"),
    ("healthy-office-snacks",       "Healthy Office Snacks",                    "General","30k+"),
    ("office-snack-subscription",   "Office Snack Subscription",                "General","10k+"),
    ("bulk-candy-for-office",       "Bulk Candy for Office",                    "Products","10k+"),
    ("office-snack-ideas",          "Office Snack Ideas",                       "Informational","20k+"),
    ("best-office-snacks",          "Best Office Snacks",                       "Products","30k+"),
    ("cheap-office-snacks-bulk",    "Cheap Office Snacks in Bulk",              "Products","10k+"),
    ("how-to-stock-breakroom",      "How to Stock an Office Breakroom",         "How-To","5k+"),
    ("breakroom-snack-ideas",       "Breakroom Snack Ideas",                    "Informational","20k+"),
    ("office-snack-box",            "Office Snack Box",                         "Products","20k+"),
    ("warehouse115-review",         "Warehouse 115 Review",                     "Review","5k+"),
    ("green-rabbit-snacks-review",  "Green Rabbit Snacks Review",               "Review","5k+"),
    ("wholesale-snacks-office",     "Wholesale Snacks for Office",              "Products","10k+"),
    ("office-snack-delivery-bulk",  "Bulk Office Snack Delivery",               "Products","10k+"),
    ("healthy-breakroom-snacks",    "Healthy Breakroom Snacks",                 "Products","10k+"),
    ("snacknation-alternatives",    "SnackNation Alternatives",                 "Comparison","5k+"),
    ("office-snack-delivery-cheap", "Cheap Office Snack Delivery",              "Comparison","5k+"),
    ("protein-bars-bulk-office",    "Protein Bars in Bulk for Office",          "Products","5k+"),
    ("gluten-free-office-snacks",   "Gluten Free Office Snacks Bulk",           "Products","5k+"),
    ("vegan-office-snacks",         "Vegan Office Snacks Bulk",                 "Products","5k+"),
    ("office-candy-bulk",           "Office Candy Bulk",                        "Products","10k+"),
    ("drinks-for-office-bulk",      "Bulk Drinks for Office",                   "Products","5k+"),
    ("fresh-fruit-office-delivery", "Fresh Fruit Office Delivery",              "Products","5k+"),
    ("office-snack-delivery-companies","Office Snack Delivery Companies",       "Comparison","10k+"),
    ("team-snacks-office",          "Team Snacks for Office",                   "General","5k+"),
    ("meeting-room-snacks",         "Meeting Room Snacks Bulk",                 "Products","5k+"),
    ("reception-desk-candy",        "Reception Desk Candy Bulk",                "Products","5k+"),
    ("individual-snack-packs-bulk", "Individual Snack Packs Bulk",              "Products","10k+"),
    ("office-wellness-snacks",      "Office Wellness Snacks",                   "Products","5k+"),
    ("holiday-office-snacks",       "Holiday Office Snacks Bulk",               "Products","5k+"),
]

# Category-specific keyword pages
CAT_KW = []
for cat_slug, cat_name, cat_desc in CATEGORIES:
    bases = [
        (f"bulk-{cat_slug}-office",     f"Bulk {cat_name} for Office",          "Products","5k+"),
        (f"office-{cat_slug}-delivery", f"Office {cat_name} Delivery",          "Products","5k+"),
        (f"best-{cat_slug}-office",     f"Best {cat_name} for Office Breakroom","Products","5k+"),
        (f"{cat_slug}-bulk-wholesale",  f"{cat_name} Bulk Wholesale",           "Products","3k+"),
        (f"breakroom-{cat_slug}",       f"Breakroom {cat_name}",                "Products","5k+"),
    ]
    CAT_KW.extend(bases)

# US State geo pages — "office snack delivery in [State]"
STATES = [
    ("alabama","Alabama"),("alaska","Alaska"),("arizona","Arizona"),("arkansas","Arkansas"),
    ("california","California"),("colorado","Colorado"),("connecticut","Connecticut"),
    ("delaware","Delaware"),("florida","Florida"),("georgia","Georgia"),("hawaii","Hawaii"),
    ("idaho","Idaho"),("illinois","Illinois"),("indiana","Indiana"),("iowa","Iowa"),
    ("kansas","Kansas"),("kentucky","Kentucky"),("louisiana","Louisiana"),("maine","Maine"),
    ("maryland","Maryland"),("massachusetts","Massachusetts"),("michigan","Michigan"),
    ("minnesota","Minnesota"),("mississippi","Mississippi"),("missouri","Missouri"),
    ("montana","Montana"),("nebraska","Nebraska"),("nevada","Nevada"),
    ("new-hampshire","New Hampshire"),("new-jersey","New Jersey"),("new-mexico","New Mexico"),
    ("new-york","New York"),("north-carolina","North Carolina"),("north-dakota","North Dakota"),
    ("ohio","Ohio"),("oklahoma","Oklahoma"),("oregon","Oregon"),("pennsylvania","Pennsylvania"),
    ("rhode-island","Rhode Island"),("south-carolina","South Carolina"),
    ("south-dakota","South Dakota"),("tennessee","Tennessee"),("texas","Texas"),
    ("utah","Utah"),("vermont","Vermont"),("virginia","Virginia"),("washington","Washington"),
    ("west-virginia","West Virginia"),("wisconsin","Wisconsin"),("wyoming","Wyoming"),
]
GEO_TYPES = [
    ("office-snack-delivery","Office Snack Delivery"),
    ("bulk-office-snacks","Bulk Office Snacks"),
    ("breakroom-snack-delivery","Breakroom Snack Delivery"),
    ("healthy-office-snacks","Healthy Office Snacks"),
    ("bulk-candy-delivery","Bulk Candy Delivery"),
]
STATE_KW = [(f"{gt}-{ss}", f"{gn} in {sn}", "Geo-State","1k+")
            for ss,sn in STATES for gt,gn in GEO_TYPES]

# US Cities — top 80 office/business markets
CITIES = [
    ("new-york-ny","New York NY"),("los-angeles-ca","Los Angeles CA"),
    ("chicago-il","Chicago IL"),("houston-tx","Houston TX"),
    ("phoenix-az","Phoenix AZ"),("philadelphia-pa","Philadelphia PA"),
    ("san-antonio-tx","San Antonio TX"),("san-diego-ca","San Diego CA"),
    ("dallas-tx","Dallas TX"),("san-jose-ca","San Jose CA"),
    ("austin-tx","Austin TX"),("jacksonville-fl","Jacksonville FL"),
    ("fort-worth-tx","Fort Worth TX"),("columbus-oh","Columbus OH"),
    ("charlotte-nc","Charlotte NC"),("indianapolis-in","Indianapolis IN"),
    ("san-francisco-ca","San Francisco CA"),("seattle-wa","Seattle WA"),
    ("denver-co","Denver CO"),("nashville-tn","Nashville TN"),
    ("washington-dc","Washington DC"),("boston-ma","Boston MA"),
    ("las-vegas-nv","Las Vegas NV"),("portland-or","Portland OR"),
    ("louisville-ky","Louisville KY"),("baltimore-md","Baltimore MD"),
    ("milwaukee-wi","Milwaukee WI"),("albuquerque-nm","Albuquerque NM"),
    ("tucson-az","Tucson AZ"),("fresno-ca","Fresno CA"),
    ("sacramento-ca","Sacramento CA"),("atlanta-ga","Atlanta GA"),
    ("kansas-city-mo","Kansas City MO"),("omaha-ne","Omaha NE"),
    ("raleigh-nc","Raleigh NC"),("minneapolis-mn","Minneapolis MN"),
    ("tampa-fl","Tampa FL"),("new-orleans-la","New Orleans LA"),
    ("wichita-ks","Wichita KS"),("riverside-ca","Riverside CA"),
    ("cincinnati-oh","Cincinnati OH"),("pittsburgh-pa","Pittsburgh PA"),
    ("orlando-fl","Orlando FL"),("st-louis-mo","St. Louis MO"),
    ("plano-tx","Plano TX"),("anchorage-ak","Anchorage AK"),
    ("irvine-ca","Irvine CA"),("scottsdale-az","Scottsdale AZ"),
    ("norfolk-va","Norfolk VA"),("madison-wi","Madison WI"),
    ("durham-nc","Durham NC"),("richmond-va","Richmond VA"),
    ("spokane-wa","Spokane WA"),("des-moines-ia","Des Moines IA"),
    ("tacoma-wa","Tacoma WA"),("akron-oh","Akron OH"),
    ("reno-nv","Reno NV"),("baton-rouge-la","Baton Rouge LA"),
    ("fremont-ca","Fremont CA"),("rochester-ny","Rochester NY"),
    ("birmingham-al","Birmingham AL"),("jersey-city-nj","Jersey City NJ"),
    ("grand-rapids-mi","Grand Rapids MI"),("huntsville-al","Huntsville AL"),
    ("salt-lake-city-ut","Salt Lake City UT"),("tulsa-ok","Tulsa OK"),
    ("tampa-fl-2","Tampa FL Metro"),("miami-fl","Miami FL"),
    ("fort-lauderdale-fl","Fort Lauderdale FL"),("hartford-ct","Hartford CT"),
    ("richmond-va-2","Richmond VA Metro"),("boise-id","Boise ID"),
    ("little-rock-ar","Little Rock AR"),("providence-ri","Providence RI"),
    ("cheyenne-wy","Cheyenne WY"),("sioux-falls-sd","Sioux Falls SD"),
    ("fargo-nd","Fargo ND"),("burlington-vt","Burlington VT"),
    ("columbia-sc","Columbia SC"),("portland-me","Portland ME"),
]
CITY_GEO_TYPES = [
    ("office-snack-delivery","Office Snack Delivery"),
    ("bulk-office-snacks","Bulk Office Snacks"),
    ("breakroom-snack-delivery","Breakroom Snack Delivery"),
]
CITY_KW = [(f"{gt}-{cs}", f"{gn} in {cn}", "Geo-City","500+")
           for cs,cn in CITIES for gt,gn in CITY_GEO_TYPES]

# Industry-specific pages
INDUSTRY_KW = [
    ("office-snacks-tech-companies",  "Office Snacks for Tech Companies",      "Niche","5k+"),
    ("office-snacks-law-firms",       "Office Snacks for Law Firms",           "Niche","3k+"),
    ("office-snacks-healthcare",      "Breakroom Snacks for Healthcare Offices","Niche","3k+"),
    ("office-snacks-real-estate",     "Office Snacks for Real Estate Teams",   "Niche","3k+"),
    ("office-snacks-startups",        "Office Snacks for Startups",            "Niche","5k+"),
    ("office-snacks-remote-hybrid",   "Snacks for Hybrid Office Teams",        "Niche","3k+"),
    ("office-snacks-small-business",  "Office Snacks for Small Business",      "Niche","5k+"),
    ("office-snacks-large-enterprise","Enterprise Office Snack Delivery",      "Niche","5k+"),
    ("breakroom-snacks-schools",      "Bulk Snacks for School Staff Rooms",    "Niche","3k+"),
    ("snacks-for-warehouse-teams",    "Bulk Snacks for Warehouse Teams",       "Niche","3k+"),
]

# Comparison pages
COMPARISON_KW = [
    ("green-rabbit-vs-snacknation",    "Green Rabbit vs SnackNation",          "Comparison","5k+"),
    ("warehouse115-vs-snack-box-pros", "Warehouse115 vs Snack Box Pros",       "Comparison","3k+"),
    ("best-office-snack-delivery-2025","Best Office Snack Delivery Services",  "Comparison","10k+"),
    ("bulk-snack-delivery-comparison", "Bulk Office Snack Delivery Comparison","Comparison","5k+"),
    ("office-snack-delivery-cheap-good","Cheap vs Premium Office Snack Delivery","Comparison","3k+"),
]

# Additional high-value keywords
EXTRA_KW = [
    ("office-pantry-service",          "Office Pantry Service",                "General","10k+"),
    ("breakroom-management-guide",     "Office Breakroom Management Guide",    "How-To","5k+"),
    ("office-snack-policy",            "Office Snack Policy Guide",            "Informational","3k+"),
    ("remote-office-snack-delivery",   "Remote Office Snack Delivery",         "General","5k+"),
    ("office-snack-delivery-no-subscription","Office Snack Delivery No Subscription","General","5k+"),
    ("bulk-snacks-free-shipping",      "Bulk Snacks with Free Shipping",       "General","5k+"),
    ("office-snack-delivery-same-day", "Office Snack Delivery Same Day",       "General","3k+"),
    ("breakroom-fresh-food-delivery",  "Breakroom Fresh Food Delivery",        "General","3k+"),
    ("warehouse115-coupon-code",       "Warehouse115 Discount Code",           "Informational","5k+"),
    ("green-rabbit-shipping-info",     "Green Rabbit Shipping Information",    "Informational","3k+"),
    ("bulk-snacks-for-events",         "Bulk Snacks for Corporate Events",     "Products","5k+"),
    ("office-kitchen-snack-ideas",     "Office Kitchen Snack Ideas",           "Informational","5k+"),
    ("bulk-food-for-office-kitchen",   "Bulk Food for Office Kitchen",         "Products","5k+"),
    ("employee-appreciation-snacks",   "Employee Appreciation Snacks Bulk",    "Products","5k+"),
    ("welcome-snack-bag-office",       "Welcome Snack Bag for New Employees",  "Products","3k+"),
    ("conference-room-snacks",         "Conference Room Snacks Bulk",          "Products","5k+"),
    ("bulk-snacks-for-employees",      "Bulk Snacks for Employees",            "Products","10k+"),
    ("onsite-office-snack-service",    "On-Site Office Snack Service",         "General","5k+"),
    ("office-snack-budget-per-person", "Office Snack Budget Per Person",       "Informational","3k+"),
    ("best-snacks-for-long-meetings",  "Best Snacks for Long Meetings",        "Products","5k+"),
]

EN_KEYWORDS = (GENERAL_KW + CAT_KW + INDUSTRY_KW + COMPARISON_KW
               + EXTRA_KW + STATE_KW + CITY_KW)

print(f"Total keywords: {len(EN_KEYWORDS):,}")
print(f"  General: {len(GENERAL_KW)} | Cat: {len(CAT_KW)} | Industry: {len(INDUSTRY_KW)}")
print(f"  Comparison: {len(COMPARISON_KW)} | State: {len(STATE_KW)} | City: {len(CITY_KW)}")

# ── CSS ─────────────────────────────────────────────────────────────────────
CSS = (
"*{box-sizing:border-box;margin:0;padding:0}"
"body{font-family:'Segoe UI',system-ui,sans-serif;color:#111827;background:#f7fdf4;line-height:1.75}"
"a{color:#16a34a;text-decoration:none}a:hover{text-decoration:underline}"
".site-header{background:#14532d;color:#fff;position:sticky;top:0;z-index:300;border-bottom:3px solid #22c55e}"
".hd{max-width:1160px;margin:0 auto;display:flex;align-items:center;justify-content:space-between;height:62px;padding:0 1.2rem}"
".logo{font-size:1.1rem;font-weight:900;color:#fff;display:flex;align-items:center;gap:.5rem}"
".logo-ico{background:#22c55e;color:#14532d;font-size:1.1rem;width:36px;height:36px;border-radius:8px;display:flex;align-items:center;justify-content:center;flex-shrink:0;font-weight:900}"
".nav-links{display:flex;gap:1.4rem;align-items:center}"
".nav-links a{color:rgba(255,255,255,.85);font-size:.82rem;font-weight:500}"
".nav-links a:hover{color:#86efac;text-decoration:none}"
".nav-cta{background:#22c55e;color:#14532d!important;font-weight:900!important;padding:.38rem 1.05rem;border-radius:6px;font-size:.82rem!important}"
".hero{background:linear-gradient(135deg,#14532d 0%,#166534 50%,#15803d 100%);color:#fff;padding:4.5rem 1.2rem 4rem;text-align:center;position:relative;overflow:hidden}"
".hero::before{content:'';position:absolute;top:-60px;right:-60px;width:350px;height:350px;background:rgba(34,197,94,.1);border-radius:50%}"
".hero-inner{max-width:860px;margin:0 auto;position:relative;z-index:1}"
".hero-eyebrow{display:inline-flex;align-items:center;gap:.5rem;background:rgba(34,197,94,.2);border:1px solid rgba(34,197,94,.5);color:#bbf7d0;border-radius:50px;padding:.3rem 1rem;font-size:.72rem;letter-spacing:1.8px;text-transform:uppercase;margin-bottom:1.5rem;font-weight:700}"
".hero h1{font-size:clamp(1.9rem,4.5vw,3rem);font-weight:900;line-height:1.12;margin-bottom:1.1rem;letter-spacing:-.5px}"
".hero h1 span{color:#86efac}"
".hero-sub{font-size:1.05rem;opacity:.88;max-width:680px;margin:0 auto 2.4rem;line-height:1.78}"
".cta-btn{display:inline-flex;align-items:center;gap:.6rem;background:#22c55e;color:#14532d;font-size:1.05rem;font-weight:900;padding:1.05rem 2.8rem;border-radius:9px;text-decoration:none;box-shadow:0 6px 28px rgba(34,197,94,.4);transition:transform .18s,box-shadow .18s}"
".cta-btn:hover{transform:translateY(-3px);box-shadow:0 10px 38px rgba(34,197,94,.5);text-decoration:none;color:#14532d}"
".hero-note{font-size:.78rem;opacity:.65;margin-top:1rem}"
".update-badge{display:inline-block;background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.25);color:rgba(255,255,255,.9);border-radius:20px;padding:.22rem .75rem;font-size:.7rem;font-weight:700;margin-top:.9rem;letter-spacing:.5px}"
".trust-strip{background:#fff;border-bottom:1px solid #bbf7d0;padding:1rem 1.2rem}"
".trust-inner{max-width:1160px;margin:0 auto;display:flex;flex-wrap:wrap;justify-content:center;gap:1.6rem}"
".trust-item{display:flex;align-items:center;gap:.42rem;font-size:.82rem;color:#374151;font-weight:600}"
".trust-ico{width:20px;height:20px;background:#16a34a;border-radius:50%;color:#fff;font-size:10px;display:flex;align-items:center;justify-content:center;flex-shrink:0}"
".stat-row{background:#dcfce7;border-bottom:2px solid #bbf7d0;padding:1.8rem 1.2rem}"
".stat-inner{max-width:1160px;margin:0 auto;display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:1rem;text-align:center}"
".stat-n{font-size:2rem;font-weight:900;color:#14532d;line-height:1}"
".stat-l{font-size:.74rem;color:#16a34a;margin-top:.3rem;font-weight:600}"
".breadcrumb{max-width:1160px;margin:0 auto;padding:.72rem 1.2rem;font-size:.79rem;color:#6b7280}"
".breadcrumb a{color:#16a34a}.breadcrumb .sep{margin:0 .32rem;color:#d1d5db}"
".pg{max-width:1160px;margin:0 auto;padding:2.2rem 1.2rem 3.5rem;display:grid;grid-template-columns:1fr 315px;gap:2.8rem;align-items:start}"
".art h2{font-size:1.28rem;font-weight:800;color:#14532d;margin:2.5rem 0 .78rem;padding-top:1.2rem;border-top:2px solid #dcfce7;line-height:1.3}"
".art h2:first-of-type{border-top:none;margin-top:0;padding-top:0}"
".art h3{font-size:1rem;font-weight:700;color:#16a34a;margin:1.5rem 0 .48rem}"
".art p{margin-bottom:1.05rem;color:#374151;font-size:.96rem;line-height:1.8}"
".art ul,.art ol{margin:0 0 1.1rem 1.45rem;color:#374151;font-size:.96rem}"
".art li{margin-bottom:.45rem;line-height:1.7}"
".art strong{color:#14532d}"
".art a{color:#16a34a}"
".intro-box{background:linear-gradient(135deg,#dcfce7,#bbf7d0);border-left:4px solid #16a34a;border-radius:0 12px 12px 0;padding:1.35rem 1.65rem;margin-bottom:2.3rem;font-size:1.01rem;color:#14532d;line-height:1.85;font-weight:500}"
".toc-box{background:#f0fdf4;border:1px solid #bbf7d0;border-radius:10px;padding:1rem 1.35rem;margin:1.2rem 0 1.8rem}"
".toc-box p{font-size:.8rem;font-weight:800;color:#14532d;margin-bottom:.55rem;text-transform:uppercase;letter-spacing:.8px}"
".toc-box ol{margin:0 0 0 1rem;padding:0;font-size:.83rem;color:#16a34a;line-height:2}"
".product-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:1.2rem;margin:1.2rem 0 1.6rem}"
".product-card{background:#fff;border:1px solid #bbf7d0;border-radius:14px;padding:1.35rem;display:flex;flex-direction:column;transition:transform .18s,box-shadow .18s}"
".product-card:hover{transform:translateY(-3px);box-shadow:0 8px 28px rgba(20,83,45,.1)}"
".product-badge{display:inline-block;background:#dcfce7;color:#14532d;font-size:.7rem;font-weight:800;padding:.22rem .6rem;border-radius:20px;margin-bottom:.65rem;text-transform:uppercase;letter-spacing:.5px}"
".product-card h3{font-size:.92rem;font-weight:800;color:#14532d;margin-bottom:.35rem}"
".product-price{font-size:1.05rem;font-weight:900;color:#16a34a;margin:.35rem 0}"
".product-count{font-size:.78rem;color:#6b7280;margin-bottom:.65rem}"
".product-card p{font-size:.82rem;color:#6b7280;line-height:1.6;margin-bottom:.9rem;flex:1}"
".buy-btn{display:block;background:#16a34a;color:#fff;font-weight:700;padding:.72rem 1rem;border-radius:8px;text-decoration:none;text-align:center;font-size:.86rem;transition:background .15s;margin-top:auto}"
".buy-btn:hover{background:#15803d;text-decoration:none;color:#fff}"
".cmp{width:100%;border-collapse:collapse;margin:1rem 0 1.6rem;font-size:.86rem;border-radius:10px;overflow:hidden;box-shadow:0 1px 8px rgba(0,0,0,.08)}"
".cmp th{background:#14532d;color:#fff;padding:.78rem 1rem;text-align:left;font-weight:700;font-size:.82rem}"
".cmp td{padding:.7rem 1rem;border-bottom:1px solid #e5e7eb;color:#374151;vertical-align:middle}"
".cmp tr:last-child td{border:none}"
".cmp tr:nth-child(even) td{background:#f0fdf4}"
".good{color:#16a34a;font-weight:700}.bad{color:#dc2626;font-weight:700}.ok{color:#d97706;font-weight:700}"
".tip-box{background:#f0fdf4;border:1px solid #bbf7d0;border-left:4px solid #22c55e;border-radius:0 10px 10px 0;padding:1.1rem 1.35rem;margin:1.5rem 0}"
".tip-box strong{color:#14532d;display:block;margin-bottom:.38rem;font-size:.93rem}"
".tip-box p{margin:0;color:#166534;font-size:.89rem}"
".steps{list-style:none;margin:0 0 1.6rem;padding:0;counter-reset:step}"
".steps li{display:flex;gap:1rem;align-items:flex-start;margin-bottom:1rem;padding:1.05rem 1.15rem;background:#fff;border:1px solid #bbf7d0;border-radius:10px;counter-increment:step}"
".steps li::before{content:counter(step);background:#16a34a;color:#fff;font-weight:900;font-size:.82rem;min-width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;flex-shrink:0;margin-top:2px}"
".steps li p{margin:0;font-size:.92rem;color:#374151;line-height:1.65}"
".steps li strong{display:block;margin-bottom:.22rem;color:#14532d;font-size:.94rem}"
".faq-wrap{margin:.6rem 0 1.6rem}"
".faq-item{border:1px solid #bbf7d0;border-radius:10px;margin-bottom:.78rem;overflow:hidden;background:#fff}"
".faq-q{background:#f0fdf4;padding:1.05rem 1.2rem;font-weight:700;color:#14532d;font-size:.93rem;cursor:pointer;list-style:none;display:flex;justify-content:space-between;align-items:center;gap:1rem}"
".faq-q::after{content:'+';font-size:1.2rem;color:#6b7280;flex-shrink:0}"
".faq-item[open] .faq-q{background:#dcfce7}"
".faq-item[open] .faq-q::after{content:'-';color:#16a34a}"
".faq-a{padding:1.05rem 1.2rem;font-size:.92rem;color:#374151;line-height:1.75;border-top:1px solid #bbf7d0}"
".pros-cons{display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin:1.2rem 0 1.6rem}"
".pros,.cons{border-radius:10px;padding:1.2rem 1.4rem}"
".pros{background:#f0fdf4;border:1px solid #bbf7d0}"
".cons{background:#fef2f2;border:1px solid #fecaca}"
".pros h4{color:#14532d;font-size:.88rem;font-weight:800;margin-bottom:.65rem;text-transform:uppercase;letter-spacing:.5px}"
".cons h4{color:#991b1b;font-size:.88rem;font-weight:800;margin-bottom:.65rem;text-transform:uppercase;letter-spacing:.5px}"
".pros li,.cons li{font-size:.85rem;margin-bottom:.4rem;list-style:none;display:flex;align-items:flex-start;gap:.4rem}"
".pros li::before{content:'✓';color:#16a34a;font-weight:900;flex-shrink:0}"
".cons li::before{content:'✗';color:#dc2626;font-weight:900;flex-shrink:0}"
".related-wrap{background:#f0fdf4;border:1px solid #bbf7d0;border-radius:12px;padding:1.45rem;margin-top:2.3rem}"
".related-wrap h3{font-size:.95rem;font-weight:800;color:#14532d;margin-bottom:.95rem}"
".rel-grid{display:grid;grid-template-columns:1fr 1fr;gap:.48rem}"
".rel-grid a{font-size:.82rem;color:#16a34a;padding:.28rem 0;display:block;font-weight:500}"
".disclosure{background:#fef9c3;border:1px solid #fde047;border-radius:9px;padding:1rem 1.2rem;font-size:.76rem;color:#854d0e;margin-top:2.2rem;line-height:1.7}"
".sidebar{position:sticky;top:74px}"
".sb-hero{background:#14532d;color:#fff;border-radius:14px;padding:1.55rem;text-align:center;margin-bottom:1.3rem;border-bottom:3px solid #22c55e}"
".sb-hero h3{color:#fff;font-size:1.02rem;margin-bottom:.48rem;font-weight:900}"
".sb-hero p{color:rgba(255,255,255,.8);font-size:.82rem;margin-bottom:1.1rem;line-height:1.65}"
".sb-btn{display:block;background:#22c55e;color:#14532d;font-weight:900;padding:.85rem;border-radius:9px;text-decoration:none;font-size:.95rem;transition:transform .18s;text-align:center}"
".sb-btn:hover{transform:translateY(-2px);text-decoration:none;color:#14532d}"
".sb-card{background:#fff;border:1px solid #bbf7d0;border-radius:14px;padding:1.3rem;margin-bottom:1.25rem}"
".sb-card h3{font-size:.92rem;font-weight:800;color:#14532d;margin-bottom:.88rem;padding-bottom:.65rem;border-bottom:2px solid #dcfce7}"
".chk-list{list-style:none;margin:0}"
".chk-list li{display:flex;align-items:flex-start;gap:.5rem;margin-bottom:.52rem;font-size:.84rem;color:#374151;line-height:1.55}"
".chk-list li::before{content:'✓';color:#16a34a;font-weight:900;flex-shrink:0}"
".blog-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(295px,1fr));gap:1.5rem;margin-top:1.6rem}"
".blog-card{background:#fff;border:1px solid #bbf7d0;border-radius:14px;padding:1.4rem;display:flex;flex-direction:column;transition:transform .18s,box-shadow .18s}"
".blog-card:hover{transform:translateY(-3px);box-shadow:0 8px 28px rgba(20,83,45,.1)}"
".blog-tag{font-size:.7rem;font-weight:800;color:#16a34a;text-transform:uppercase;letter-spacing:1px;margin-bottom:.5rem}"
".blog-card h3{font-size:.98rem;font-weight:700;color:#14532d;margin-bottom:.5rem;line-height:1.42;flex:1}"
".blog-meta{display:flex;justify-content:space-between;align-items:center;font-size:.74rem;color:#9ca3af;margin-top:auto;padding-top:.6rem}"
".blog-read{color:#16a34a;font-weight:700}"
".share-bar{display:flex;align-items:center;gap:.6rem;margin:1.8rem 0;padding:1rem 1.2rem;background:#f0fdf4;border-radius:10px;border:1px solid #bbf7d0;flex-wrap:wrap}"
".share-btn{display:inline-flex;align-items:center;gap:.38rem;padding:.38rem .85rem;border-radius:6px;font-size:.78rem;font-weight:700;cursor:pointer;border:none;transition:transform .15s}"
".sh-fb{background:#1877f2;color:#fff}.sh-tw{background:#1da1f2;color:#fff}.sh-li{background:#0077b5;color:#fff}.sh-cp{background:#e5e7eb;color:#374151}"
".share-btn:hover{transform:translateY(-1px)}"
".author-bar{display:flex;align-items:center;gap:.75rem;padding:.85rem 1.1rem;background:#f0fdf4;border-radius:10px;border:1px solid #bbf7d0;margin-bottom:1.5rem}"
".author-av{width:38px;height:38px;background:#16a34a;border-radius:50%;display:flex;align-items:center;justify-content:center;color:#fff;font-weight:900;font-size:.85rem;flex-shrink:0}"
".author-name{font-size:.86rem;font-weight:700;color:#14532d}"
".author-title{font-size:.76rem;color:#6b7280}"
".verified-badge{display:inline-block;background:#dcfce7;color:#14532d;font-size:.68rem;font-weight:700;padding:.15rem .45rem;border-radius:4px;margin-left:.4rem}"
".ph{background:#14532d;color:#fff;padding:2.8rem 1.2rem 2.4rem;text-align:center;border-bottom:3px solid #22c55e}"
".ph h1{font-size:clamp(1.7rem,3.2vw,2.1rem);font-weight:900;color:#fff;margin-bottom:.7rem}"
".ph p{opacity:.88;max-width:540px;margin:0 auto;font-size:.97rem;line-height:1.72}"
".section{max-width:1160px;margin:0 auto;padding:3rem 1.2rem}"
".section-h{font-size:1.75rem;font-weight:900;color:#14532d;margin-bottom:.55rem}"
".section-sub{color:#6b7280;margin-bottom:2rem;font-size:.96rem}"
".how-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:1.3rem;margin-top:1.6rem}"
".how-step{background:#fff;border:1px solid #bbf7d0;border-radius:14px;padding:1.5rem;text-align:center}"
".how-num{width:50px;height:50px;background:#14532d;color:#86efac;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:1.3rem;font-weight:900;margin:0 auto 1.1rem}"
".how-step h3{font-size:.94rem;font-weight:800;color:#14532d;margin-bottom:.4rem}"
".how-step p{font-size:.82rem;color:#6b7280;line-height:1.62}"
".cat-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:1.1rem;margin-top:1.5rem}"
".cat-card{background:#fff;border:1px solid #bbf7d0;border-radius:12px;padding:1.2rem;transition:transform .18s}"
".cat-card:hover{transform:translateY(-2px)}"
".cat-card h3{font-size:.92rem;font-weight:800;color:#14532d;margin-bottom:.3rem}"
".cat-card p{font-size:.8rem;color:#6b7280;margin:0}"
".footer{background:#052e16;color:#86efac;padding:3.5rem 1.2rem 2rem}"
".footer-inner{max-width:1160px;margin:0 auto}"
".footer-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(175px,1fr));gap:2.2rem;margin-bottom:2.2rem}"
".footer-col h4{color:#bbf7d0;font-size:.86rem;margin-bottom:.88rem;font-weight:900;letter-spacing:.4px;text-transform:uppercase}"
".footer-col a{display:block;color:#86efac;font-size:.81rem;margin-bottom:.38rem;transition:color .15s}"
".footer-col a:hover{color:#bbf7d0;text-decoration:none}"
".footer-bottom{border-top:1px solid rgba(255,255,255,.07);padding-top:1.25rem;font-size:.74rem;text-align:center;line-height:1.85;color:#4ade80}"
"@media(max-width:768px){.pg{grid-template-columns:1fr}.sidebar{position:static}.nav-links{display:none}.rel-grid{grid-template-columns:1fr}.hero{padding:3rem 1.2rem 2.5rem}.pros-cons{grid-template-columns:1fr}}"
)

JS = """<script>
document.querySelectorAll('.faq-item').forEach(function(d){
  d.querySelector('.faq-q').addEventListener('click',function(){
    var o=d.hasAttribute('open');
    document.querySelectorAll('.faq-item[open]').forEach(function(x){x.removeAttribute('open')});
    if(!o)d.setAttribute('open','');
  });
});
document.querySelectorAll('.share-btn').forEach(function(b){
  b.addEventListener('click',function(){
    var url=b.dataset.url||window.location.href,n=b.dataset.network;
    if(n==='facebook')window.open('https://www.facebook.com/sharer/sharer.php?u='+encodeURIComponent(url),'_blank','width=600,height=400');
    else if(n==='twitter')window.open('https://twitter.com/intent/tweet?url='+encodeURIComponent(url),'&text='+encodeURIComponent(document.title),'_blank','width=600,height=400');
    else if(n==='linkedin')window.open('https://www.linkedin.com/sharing/share-offsite/?url='+encodeURIComponent(url),'_blank','width=600,height=400');
    else if(n==='copy'){if(navigator.clipboard)navigator.clipboard.writeText(url);b.textContent='Copied!';setTimeout(function(){b.textContent='Copy Link'},2000);}
  });
});
</script>"""

# ── SHARED COMPONENTS ─────────────────────────────────────────────────────────
def hd(title, desc, canon, schemas=None, og_type="website"):
    desc = desc[:158]
    sc   = "\n".join(f'<script type="application/ld+json">{s}</script>' for s in (schemas or []))
    return f"""<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta name="google-site-verification" content="{GOOGLE_V}">
<meta name="msvalidate.01" content="{BING_V}">
<meta name="robots" content="index,follow,max-snippet:-1,max-image-preview:large">
<link rel="canonical" href="{canon}">
<meta property="og:type" content="{og_type}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{canon}">
<meta property="og:site_name" content="{NAME}">
<meta property="og:image" content="{OG}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{desc}">
<meta name="twitter:image" content="{OG}">
{sc}
<style>{CSS}</style>"""

def nav():
    return f"""<header class="site-header">
<div class="hd">
<a href="{SITE}/" class="logo"><div class="logo-ico">🐇</div>{NAME}</a>
<nav class="nav-links">
<a href="{SITE}/">Home</a>
<a href="{SITE}/guides/">Guides</a>
<a href="{SITE}/guides/best-office-snacks/">Best Snacks</a>
<a href="{SITE}/blog/">Blog</a>
<a href="{AFF}" class="nav-cta" rel="noopener sponsored">Shop Now</a>
</nav>
</div>
</header>"""

def trust():
    items = ["425+ Snack Products","Free Shipping on Orders","Bulk Quantities Available",
             "Same-Day Processing","USA Contiguous Delivery","Fresh Food Guaranteed"]
    inner = "".join(f'<div class="trust-item"><div class="trust-ico">✓</div>{i}</div>' for i in items)
    return f'<div class="trust-strip"><div class="trust-inner">{inner}</div></div>'

def footer():
    return f"""<footer class="footer">
<div class="footer-inner">
<div class="footer-grid">
<div class="footer-col">
<h4>{NAME}</h4>
<p style="font-size:.8rem;line-height:1.7;margin-bottom:.9rem;color:#86efac">Independent affiliate site. We earn commissions on qualifying purchases at no extra cost to you.</p>
<a href="{AFF}" style="color:#bbf7d0;font-weight:900;font-size:.88rem" rel="noopener sponsored">Shop Green Rabbit →</a>
</div>
<div class="footer-col">
<h4>Top Guides</h4>
<a href="{SITE}/guides/office-snack-delivery/">Office Snack Delivery</a>
<a href="{SITE}/guides/bulk-office-snacks/">Bulk Office Snacks</a>
<a href="{SITE}/guides/healthy-office-snacks/">Healthy Office Snacks</a>
<a href="{SITE}/guides/best-office-snacks/">Best Office Snacks</a>
<a href="{SITE}/guides/breakroom-snacks/">Breakroom Snacks</a>
<a href="{SITE}/guides/warehouse115-review/">Warehouse115 Review</a>
</div>
<div class="footer-col">
<h4>Categories</h4>
<a href="{SITE}/guides/bulk-candy-for-office/">Office Candy</a>
<a href="{SITE}/guides/protein-bars-bulk-office/">Protein Bars</a>
<a href="{SITE}/guides/drinks-for-office-bulk/">Office Drinks</a>
<a href="{SITE}/guides/nuts-trail-mix-bulk-wholesale/">Nuts & Trail Mix</a>
<a href="{SITE}/guides/fresh-fruit-office-delivery/">Fresh Fruit</a>
<a href="{SITE}/guides/individual-snack-packs-bulk/">Snack Packs</a>
</div>
<div class="footer-col">
<h4>Resources</h4>
<a href="{SITE}/guides/how-to-stock-breakroom/">How to Stock a Breakroom</a>
<a href="{SITE}/guides/office-snack-ideas/">Snack Ideas</a>
<a href="{SITE}/guides/gluten-free-office-snacks/">Gluten-Free Options</a>
<a href="{SITE}/guides/vegan-office-snacks/">Vegan Options</a>
<a href="{SITE}/guides/green-rabbit-vs-snacknation/">Green Rabbit vs SnackNation</a>
<a href="{SITE}/about.html">About</a>
</div>
</div>
<div class="footer-bottom">
<p>© {YEAR} {NAME} — Independent affiliate resource. Not affiliated with Warehouse 115 or Green Rabbit beyond the affiliate programme. We earn commissions on qualifying purchases.</p>
</div>
</div>
</footer>"""

def share(url):
    return f"""<div class="share-bar">
<span style="font-size:.82rem;font-weight:700;color:#374151;margin-right:.3rem">Share:</span>
<button class="share-btn sh-fb" data-network="facebook" data-url="{url}">Facebook</button>
<button class="share-btn sh-tw" data-network="twitter" data-url="{url}">Twitter/X</button>
<button class="share-btn sh-li" data-network="linkedin" data-url="{url}">LinkedIn</button>
<button class="share-btn sh-cp" data-network="copy" data-url="{url}">Copy Link</button>
</div>"""

def author_bar(html_content):
    mins = read_mins(html_content)
    wc_n = wc(html_content)
    return f"""<div class="author-bar">
<div class="author-av">GR</div>
<div>
<div class="author-name">{NAME} Editorial<span class="verified-badge">✓ Office Snack Expert</span></div>
<div class="author-title">Updated <time datetime="{TODAY}">{TODAY}</time> · {mins} min read · {wc_n:,} words · Sources: Warehouse115, Green Rabbit</div>
</div>
</div>"""

def product_grid(slug, idx, limit=4):
    """Show a rotating selection of real products."""
    start = (sh(slug) + idx) % len(PRODUCTS)
    selected = [PRODUCTS[(start+i) % len(PRODUCTS)] for i in range(min(limit, len(PRODUCTS)))]
    BTNS = ["Shop This Product →","Order in Bulk →","Get Bulk Price →",
            "Buy Now →","Order Today →","Get Yours →","Shop Bulk →","Buy in Bulk →"]
    cards = "".join(
        f'<div class="product-card">'
        f'<div class="product-badge">{cat.replace("-"," ").title()}</div>'
        f'<h3>{name}</h3>'
        f'<div class="product-price">{price}</div>'
        f'<div class="product-count">{count} per case</div>'
        f'<p>{desc}</p>'
        f'<a href="{AFF}" class="buy-btn" rel="noopener sponsored">{BTNS[(sh(slug)+i)%len(BTNS)]}</a>'
        f'</div>'
        for i,(pslug,name,price,count,cat,desc) in enumerate(selected)
    )
    return f'<div class="product-grid">{cards}</div>'

def stat_block():
    return """<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:.85rem;margin:1.2rem 0 1.5rem">
<div style="background:#dcfce7;border-radius:10px;padding:1rem;text-align:center"><div style="font-size:1.6rem;font-weight:900;color:#14532d">425+</div><div style="font-size:.75rem;color:#16a34a;margin-top:.3rem;font-weight:600">Products available</div></div>
<div style="background:#dcfce7;border-radius:10px;padding:1rem;text-align:center"><div style="font-size:1.6rem;font-weight:900;color:#14532d">Free</div><div style="font-size:.75rem;color:#16a34a;margin-top:.3rem;font-weight:600">Shipping included</div></div>
<div style="background:#dcfce7;border-radius:10px;padding:1rem;text-align:center"><div style="font-size:1.6rem;font-weight:900;color:#14532d">Bulk</div><div style="font-size:.75rem;color:#16a34a;margin-top:.3rem;font-weight:600">Case quantities</div></div>
<div style="background:#dcfce7;border-radius:10px;padding:1rem;text-align:center"><div style="font-size:1.6rem;font-weight:900;color:#14532d">USA</div><div style="font-size:.75rem;color:#16a34a;margin-top:.3rem;font-weight:600">Contiguous US delivery</div></div>
</div>"""

# 30 internal links
IL_POOL = [
    f'<a href="{SITE}/guides/office-snack-delivery/">office snack delivery</a>',
    f'<a href="{SITE}/guides/bulk-office-snacks/">bulk office snacks</a>',
    f'<a href="{SITE}/guides/healthy-office-snacks/">healthy office snacks</a>',
    f'<a href="{SITE}/guides/breakroom-snacks/">breakroom snack ideas</a>',
    f'<a href="{SITE}/guides/best-office-snacks/">best office snacks</a>',
    f'<a href="{SITE}/guides/how-to-stock-breakroom/">how to stock a breakroom</a>',
    f'<a href="{SITE}/guides/warehouse115-review/">Warehouse115 review</a>',
    f'<a href="{SITE}/guides/bulk-candy-for-office/">bulk office candy</a>',
    f'<a href="{SITE}/guides/protein-bars-bulk-office/">bulk protein bars</a>',
    f'<a href="{SITE}/guides/drinks-for-office-bulk/">bulk office drinks</a>',
    f'<a href="{SITE}/guides/nuts-trail-mix-bulk-wholesale/">bulk nuts and trail mix</a>',
    f'<a href="{SITE}/guides/fresh-fruit-office-delivery/">fresh fruit delivery</a>',
    f'<a href="{SITE}/guides/office-snack-ideas/">office snack ideas</a>',
    f'<a href="{SITE}/guides/individual-snack-packs-bulk/">individual snack packs bulk</a>',
    f'<a href="{SITE}/guides/gluten-free-office-snacks/">gluten-free office snacks</a>',
    f'<a href="{SITE}/guides/vegan-office-snacks/">vegan office snacks</a>',
    f'<a href="{SITE}/guides/green-rabbit-vs-snacknation/">Green Rabbit vs SnackNation</a>',
    f'<a href="{SITE}/guides/office-snack-delivery-companies/">office snack delivery companies</a>',
    f'<a href="{SITE}/guides/corporate-snack-delivery/">corporate snack delivery</a>',
    f'<a href="{SITE}/guides/meeting-room-snacks/">meeting room snack guide</a>',
    f'<a href="{SITE}/guides/reception-desk-candy/">reception desk candy</a>',
    f'<a href="{SITE}/guides/office-wellness-snacks/">office wellness snacks</a>',
    f'<a href="{SITE}/guides/employee-snacks/">employee snack guide</a>',
    f'<a href="{SITE}/guides/bulk-snacks-for-work/">bulk snacks for work</a>',
    f'<a href="{SITE}/guides/office-snack-box/">office snack box review</a>',
    f'<a href="{SITE}/guides/wholesale-snacks-office/">wholesale office snacks</a>',
    f'<a href="{SITE}/guides/office-snacks-startups/">startup office snack guide</a>',
    f'<a href="{SITE}/guides/office-snacks-tech-companies/">tech company snack guide</a>',
    f'<a href="{SITE}/blog/how-to-stock-breakroom-guide/">breakroom stocking guide</a>',
    f'<a href="{SITE}/blog/best-office-snacks-2025/">best office snacks 2025</a>',
    # Extra slugs to improve IL diversity
    f'<a href="{SITE}/guides/office-snack-subscription/">office snack subscription guide</a>',
    f'<a href="{SITE}/guides/corporate-snack-delivery/">corporate snack delivery</a>',
    f'<a href="{SITE}/guides/team-snacks-office/">team snacks for the office</a>',
    f'<a href="{SITE}/guides/cheap-office-snacks-bulk/">cheap bulk office snacks</a>',
    f'<a href="{SITE}/guides/office-food-delivery/">office food delivery guide</a>',
    f'<a href="{SITE}/guides/healthy-breakroom-snacks/">healthy breakroom snacks</a>',
    f'<a href="{SITE}/guides/bulk-snacks-for-work/">bulk snacks for work</a>',
    f'<a href="{SITE}/blog/warehouse115-vs-costco/">Warehouse115 vs Costco comparison</a>',
    f'<a href="{SITE}/blog/bulk-snacks-vs-subscription/">bulk vs subscription comparison</a>',
    f'<a href="{SITE}/blog/office-snack-budget-guide/">office snack budget guide</a>',
    f'<a href="{SITE}/blog/office-snack-ideas-teams/">30 office snack ideas</a>',
    f'<a href="{SITE}/blog/green-rabbit-warehouse115-review/">Green Rabbit review</a>',
]
def il(slug, n):
    # Mix slug hash with n using prime multiplication for better distribution
    return IL_POOL[(sh(slug + str(n)) + n * 1117) % len(IL_POOL)]

RELATED = {
    "General":[("office-snack-delivery","Snack Delivery"),("bulk-office-snacks","Bulk Snacks"),
               ("healthy-office-snacks","Healthy Options"),("best-office-snacks","Best Snacks"),
               ("breakroom-snacks","Breakroom Ideas"),("how-to-stock-breakroom","Stock a Breakroom")],
    "Products":[("bulk-office-snacks","Bulk Snacks"),("individual-snack-packs-bulk","Snack Packs"),
                ("best-office-snacks","Best Options"),("cheap-office-snacks-bulk","Budget Snacks"),
                ("wholesale-snacks-office","Wholesale"),("office-snack-delivery","Delivery Guide")],
    "Informational":[("office-snack-ideas","Snack Ideas"),("how-to-stock-breakroom","Stock Breakroom"),
                     ("best-office-snacks","Best Snacks"),("healthy-office-snacks","Healthy Options"),
                     ("breakroom-snack-ideas","Breakroom Ideas"),("office-wellness-snacks","Wellness")],
    "How-To":[("breakroom-snacks","Breakroom Ideas"),("office-snack-ideas","Snack Ideas"),
              ("bulk-office-snacks","Buy in Bulk"),("healthy-office-snacks","Healthy Options"),
              ("individual-snack-packs-bulk","Individual Packs"),("office-snack-delivery","Delivery")],
    "Comparison":[("warehouse115-review","Warehouse115 Review"),("green-rabbit-snacks-review","GR Review"),
                  ("best-office-snacks","Best Snacks"),("office-snack-delivery-companies","Companies"),
                  ("cheap-office-snacks-bulk","Budget Options"),("office-snack-service","Snack Service")],
    "Review":[("best-office-snacks","Best Snacks"),("office-snack-delivery","Delivery Guide"),
              ("green-rabbit-vs-snacknation","vs SnackNation"),("office-snack-delivery-companies","Alternatives"),
              ("bulk-office-snacks","Bulk Buying"),("how-to-stock-breakroom","Stock Breakroom")],
    "Niche":[("office-snack-delivery","Delivery Guide"),("bulk-office-snacks","Bulk Snacks"),
             ("healthy-office-snacks","Healthy Options"),("office-snack-ideas","Snack Ideas"),
             ("employee-snacks","Employee Snacks"),("how-to-stock-breakroom","Stock Breakroom")],
    "Geo-State":[("office-snack-delivery","Delivery Guide"),("bulk-office-snacks","Bulk Snacks"),
                 ("healthy-office-snacks","Healthy Options"),("warehouse115-review","Warehouse115"),
                 ("how-to-stock-breakroom","Stock Breakroom"),("best-office-snacks","Best Snacks")],
    "Geo-City":[("office-snack-delivery","Delivery Guide"),("bulk-office-snacks","Bulk Snacks"),
                ("breakroom-snacks","Breakroom Ideas"),("individual-snack-packs-bulk","Snack Packs"),
                ("healthy-office-snacks","Healthy"),("warehouse115-review","Warehouse115")],
}
def get_related(cat, slug):
    pool = RELATED.get(cat, RELATED["General"])
    return [(s,t) for s,t in pool if s != slug][:6]

# ── FAQ POOLS ─────────────────────────────────────────────────────────────────
FAQ_POOLS = {
    "General":[
        ("What is Green Rabbit snack delivery?",
         "Green Rabbit is a cold-chain logistics and snack delivery service that ships bulk snacks, candy, protein bars, drinks, and fresh food to offices and businesses across the contiguous United States. Orders are fulfilled through Warehouse115 at warehouse115.com and ship via FedEx or UPS Ground with free shipping included on Green Rabbit products."),
        ("Does Green Rabbit offer free shipping?",
         "Yes. Warehouse115 provides free shipping on all Green Rabbit product orders to the contiguous United States. Orders cannot be shipped to Hawaii, Alaska, or Puerto Rico. Shipping is handled through FedEx and UPS Ground partnerships."),
        ("What types of snacks does Green Rabbit carry?",
         "Green Rabbit via Warehouse115 carries 425+ products including candy, chocolate, chips, popcorn, protein bars, energy bars, nuts, trail mix, cookies, pastries, fresh fruit, yogurt, beverages, juice, and iced tea. Products come in bulk case quantities ideal for office breakrooms, reception areas, and meeting rooms."),
        ("How quickly does Green Rabbit ship?",
         "Green Rabbit fulfills from three centers (California, Indiana, Massachusetts) reaching 95% of the contiguous US in 2 days or fewer via ground network, and 45% in just 1 day. Orders are processed same day when placed during business hours (M–F 8am–5pm EST)."),
        ("Is Green Rabbit USA-only?",
         "Yes. Green Rabbit via Warehouse115 ships only to the contiguous 48 US states. Delivery is not available to Hawaii, Alaska, Puerto Rico, or international addresses. This is because many products include fresh and temperature-sensitive items requiring fast, reliable ground delivery."),
        ("What is the minimum order for Green Rabbit?",
         "There is no stated minimum order. Products are available in individual case quantities — most come in 12, 16, 18, 24, 30, 36, 42, 50, or 65-count cases depending on the item. You can order a single case of one product or multiple cases of different items in one order."),
        ("Can I order fresh fruit and yogurt for my office?",
         "Yes. Green Rabbit via Warehouse115 carries fresh items including Fuji apples, seedless oranges, bagels, Chobani Greek yogurt, Dannon Oikos yogurt, and Dannon Danimals smoothies. These items require standard ground shipping and are packed for freshness during transit."),
        ("How does Green Rabbit compare to SnackNation?",
         "Green Rabbit via Warehouse115 focuses on bulk wholesale case buying with free shipping and no subscription required — you buy what you need when you need it. SnackNation operates a curated subscription box model with monthly fees. For offices wanting flexible bulk ordering of name-brand products at wholesale prices, Green Rabbit offers better value for most purchasing patterns."),
    ],
    "Products":[
        ("What are the most popular snacks for office breakrooms?",
         "The top-selling items for office breakrooms include individually wrapped chips (Doritos, SkinnyPop), protein bars (RXBAR, Clif Bar), nuts (Blue Diamond almonds, Planters peanuts), candy (Werther's, Dove chocolate, Ghirardelli dark chocolate), and drinks (Arizona Green Tea, Lipton Pure Leaf, Snapple). All available in bulk cases through Green Rabbit at Warehouse115."),
        ("What healthy snack options does Green Rabbit offer?",
         "Green Rabbit carries a strong healthy snack selection: Nature's Garden trail mixes, RXBAR protein bars, Clif Bars, Blue Diamond almonds, SkinnyPop 100-calorie popcorn, Chobani Greek yogurt, Black Forest organic gummy bears, fresh Fuji apples, Crystal Light drink mixes, and Lipton Pure Leaf unsweetened tea. All available in bulk case quantities."),
        ("Does Green Rabbit carry gluten-free options?",
         "Yes. Several Green Rabbit products are gluten-free, including RXBAR protein bars, Blue Diamond almonds, SkinnyPop popcorn, many Nature's Garden trail mixes, and fresh fruit items. Check individual product listings at warehouse115.com for specific dietary certifications."),
        ("What drinks are available in bulk for offices?",
         "Green Rabbit via Warehouse115 carries bulk office drinks including Arizona Green Tea (24-count), Arizona Juice Variety Pack (24-count), Lipton Pure Leaf Unsweetened Iced Tea (18-count), Snapple All Natural Juice Drink Variety Pack (24-count), Diet Snapple (24-count), and Crystal Light Lemonade and Iced Tea drink mix packets."),
        ("What candy is available in bulk for the office?",
         "Popular bulk office candy options include Werther's Original Caramel Candies, Dove Milk Chocolate Bars, Ghirardelli Intense Dark Chocolate, Black Forest Organic Gummy Bears, Andes Crème de Menthe Chocolate Mints, Red Vines Black Licorice Twists, and 100 Grand Candy Bars — all available in case quantities through Warehouse115."),
        ("Does Green Rabbit carry protein bars in bulk?",
         "Yes. Protein bar options include RXBAR Assorted Flavors (15-count), Clif Bar Energy Bar Variety Pack (24-count), and Clif Builder's 20g Protein Bar Variety Pack (18-count). All are available as full cases, ideal for stocking breakroom shelves for fitness-conscious office teams."),
        ("Are there vegan snack options available?",
         "Yes. Many Green Rabbit products are vegan, including RXBAR bars (check flavours), SkinnyPop popcorn, Nature's Garden trail mixes, Blue Diamond almonds, Planters peanuts, fresh fruit, Crystal Light drink mixes, Arizona beverages, and most hard candies. Check individual product labels for certification."),
        ("What is the best bulk snack value at Warehouse115?",
         "Top value picks include Planters Salted Peanuts (96-count for $56.80 = $0.59 per pack), Black Forest Organic Gummy Bears (65-count for $57.30 = $0.88 per pack), SkinnyPop (24-count for $46.72 = $1.95 per bag), and Doritos (50-count for $56.99 = $1.14 per bag). All include free shipping, improving the per-unit cost further."),
    ],
    "How-To":[
        ("How do I stock an office breakroom with bulk snacks?",
         "Start with a snack audit: survey your team on preferences (sweet vs savory, healthy vs indulgent, dietary restrictions). Then build a core selection: 1-2 salty snack options, 1-2 sweet options, 1-2 healthy options, and beverages. Order through Green Rabbit at Warehouse115 in bulk cases. Set a monthly restock schedule and track what disappears fastest to refine your order."),
        ("How many snacks do I need to order for my office?",
         "A general rule: order 2-3 individual snack portions per employee per week. For a 20-person office, that's 40-60 snack items per week or 160-240 per month. A case of 50 Doritos bags handles 2.5 weeks of chips for a 20-person team. Order 2-3 different snack types per restock to maintain variety."),
        ("How do I set up a breakroom candy bowl?",
         "For a reception or breakroom candy bowl, choose loose hard candies (Werther's, Andes mints, Colombina mint balls) or individually wrapped pieces that won't melt. Order a bulk case of your preferred candy, refill weekly, and keep a backup case in storage. Ghirardelli dark chocolate squares and Dove milk chocolate bars also work well for a premium candy bowl."),
        ("What snacks should I order for a company meeting?",
         "For meetings, choose individually wrapped snacks that are easy to pass around with minimal mess: Clif Bars, RXBAR, Famous Amos cookies, Nature's Garden trail mix packs, Blue Diamond almond snack packs, or SkinnyPop individual bags. For longer meetings, add bottled drinks (Snapple, Pure Leaf) and fresh fruit (Fuji apples, oranges). All available in bulk through Green Rabbit."),
        ("How do I order bulk snacks for an office party or event?",
         "For office events, order 1-2 weeks in advance to ensure delivery. Mix sweet and savory: Doritos and SkinnyPop for chips, Dove chocolate and Ghirardelli for sweets, RXBAR for health-conscious guests, Arizona drinks or Snapple for beverages. Green Rabbit via Warehouse115 processes orders same day and ships free to the contiguous US."),
        ("How do I reduce office snack costs while keeping variety?",
         "Buy in bulk (cases vs individual packs), choose high-count cases (Planters 96-count, Doritos 50-count) for maximum per-unit value, and consolidate orders to take advantage of free shipping. Rotate 3-4 snack types monthly to maintain interest without over-stocking. Green Rabbit's wholesale prices through Warehouse115 are significantly below retail for the same name-brand products."),
    ],
    "Informational":[
        ("Why should companies provide free office snacks?",
         "Research consistently shows workplace snacks improve employee satisfaction, retention, and productivity. A Snack Nation survey found 67% of employees feel happier and more productive in offices with free snacks. Snacks are a low-cost perk with high perceived value — significantly cheaper than salary increases or benefits upgrades, yet measurably improving workplace culture."),
        ("How much does it cost to stock an office breakroom?",
         "For a 20-person office, expect to spend $150-$400 per month on a well-stocked breakroom. This covers chips, candy, protein bars, and drinks ordered in bulk through Warehouse115 with free shipping. Per-employee cost: $7.50-$20/month — one of the most cost-effective employee benefits available."),
        ("What are the most popular office snack trends in 2025?",
         "The top office snack trends for 2025 include: high-protein options (RXBAR, Clif Builder's), better-for-you classics (SkinnyPop, Nature's Garden), premium chocolate (Ghirardelli, Dove), functional beverages (low-sugar teas, electrolyte drinks), fresh food delivery (yogurt, fresh fruit), and individually wrapped formats for hygiene and portion control."),
        ("What dietary restrictions should office snacks accommodate?",
         "A well-stocked office breakroom should address: gluten-free (RXBAR, almonds, SkinnyPop, fresh fruit), vegan (most nuts, trail mix, hard candies, fresh fruit), low-sugar/diabetic-friendly (Werther's Sugar Free, nuts, Crystal Light), and nut allergies (keep nut-free alternatives available). Survey your team before ordering to identify specific needs."),
        ("Is it better to buy office snacks in bulk or use a subscription?",
         "For most offices, bulk buying from a supplier like Green Rabbit via Warehouse115 is more cost-effective than a monthly subscription box. You choose exactly what products, quantities, and cadence you want with no recurring fees. Subscription boxes offer curation and discovery but cost more per item. If your office wants specific name-brand products in reliable quantities, bulk buying wins."),
        ("What makes Green Rabbit different from other office snack services?",
         "Green Rabbit via Warehouse115 differs from subscription services by offering: wholesale pricing on name-brand products you already know (not curated mystery boxes), free shipping, flexible ordering with no minimum commitment, 425+ product selection, and fresh food capability (fruit, yogurt, bagels) that most snack subscription boxes can't handle."),
    ],
    "Comparison":[
        ("Green Rabbit vs SnackNation — which is better for offices?",
         "Depends on your needs. SnackNation is a curated subscription delivering monthly snack boxes — great for discovery and convenience but you can't specify exactly what arrives. Green Rabbit via Warehouse115 lets you order exactly what you want in bulk at wholesale prices with free shipping and no subscription fees. For offices with established snack preferences, Green Rabbit offers better value and control."),
        ("How does Warehouse115 pricing compare to retail?",
         "Warehouse115 bulk prices are typically 20-40% below retail for the same products. Example: SkinnyPop 24-pack from Warehouse115 at $46.72 ($1.95/bag) vs buying 24 individual bags at retail ($2.99-$3.49 each = $72-$84). Doritos 50-count at $56.99 ($1.14/bag) vs ~$1.89-$2.29 at retail. Free shipping makes the savings even larger."),
        ("Is Green Rabbit or Amazon Business better for bulk office snacks?",
         "Amazon Business offers broad selection and fast shipping but variable pricing, inconsistent case sizing, and per-item shipping on some products. Green Rabbit via Warehouse115 specializes in office and foodservice quantities with free shipping, fresh food capability, and a curated selection of top office snack brands. For regular bulk snack ordering, Green Rabbit pricing is often more consistent."),
        ("What are the best office snack delivery services?",
         "Top office snack delivery services include: Green Rabbit via Warehouse115 (best for bulk wholesale, fresh food, no subscription), SnackNation (best for curated monthly boxes), Snack Box Pros (good for variety sampling), Amazon Business (best for speed and selection breadth), and Staples Advantage (good for consolidated office supply + snack orders). Green Rabbit wins on bulk price and fresh food options."),
        ("Can Green Rabbit handle large enterprise office snack orders?",
         "Yes. Green Rabbit via Warehouse115 is designed for business-scale ordering with no order cap. Large enterprises can order hundreds of cases at a time with free shipping on all orders. For very large or recurring enterprise programs, contact Warehouse115 directly (678-961-4606) to discuss account options."),
        ("Warehouse115 vs buying from Costco for office snacks?",
         "Costco requires membership ($65-$130/year), physical pickup (or limited delivery), and offers a narrower snack selection than Warehouse115's 425+ items. Warehouse115 ships free to your door, no membership required, with more individual snack pack options vs Costco's larger format packs. For offices without warehouse store access or those wanting delivery, Warehouse115 wins on convenience."),
    ],
    "Geo-State":[
        ("Is there a minimum order for delivery to {loc}?",
         "No minimum order for delivery to {loc}. Order a single case or multiple cases — free shipping applies to all Green Rabbit orders regardless of order size. Checkout is straightforward with no membership required."),
        ("What office snacks ship fastest to {loc}?",
         "All Green Rabbit products at Warehouse115 ship via FedEx or UPS Ground with same-day processing (M-F before 5pm EST). Most {loc} addresses receive delivery within 1-3 business days. Shelf-stable products (chips, candy, protein bars, nuts, drinks) ship from the nearest of three fulfillment centers in California, Indiana, and Massachusetts."),
        ("Can I order fresh fruit and yogurt for my {loc} office?",
         "Yes. Green Rabbit via Warehouse115 ships fresh items including Fuji apples, oranges, Chobani Greek yogurt, and Dannon yogurt to {loc} via ground delivery. Green Rabbit's cold-chain expertise ensures perishables arrive fresh. Confirm you have breakroom refrigerator space before ordering refrigerated items."),
        ("What is the best bulk snack to start with for a {loc} office?",
         "For a first order to a {loc} office, start with universally loved products: Doritos 1oz bags (50-count, $56.99), RXBAR or Clif Bars (protein), Blue Diamond almonds (healthy option), and Arizona Green Tea (24-count, $39.58). This baseline covers all four snack categories with free shipping to {loc}."),
        ("Does Green Rabbit deliver to {loc}?",
         "Yes. Green Rabbit via Warehouse115 delivers to {loc} as part of its contiguous US delivery network. Free shipping is included on all Green Rabbit orders to {loc}. Orders ship via FedEx and UPS Ground and are processed same day when placed by 5pm EST Monday-Friday."),
        ("How long does Green Rabbit take to deliver in {loc}?",
         "Most Green Rabbit orders reach {loc} within 1-3 business days depending on your location within the state. Green Rabbit operates fulfillment centers in California, Indiana, and Massachusetts — providing 95% of the contiguous US with 2-day ground delivery. Free shipping is included on all orders."),
        ("What bulk office snacks are popular in {loc}?",
         "The same top-selling national brands are popular in {loc} offices: Doritos and SkinnyPop for chips, RXBAR and Clif Bar for protein, Blue Diamond almonds and Planters peanuts for nuts, Dove chocolate and Ghirardelli for candy, and Arizona and Snapple for drinks. All available in bulk cases with free shipping to {loc} through Green Rabbit at Warehouse115."),
        ("Is there a minimum order for Green Rabbit delivery to {loc}?",
         "No stated minimum order for delivery to {loc}. You can order a single case of any product and receive free shipping. Green Rabbit via Warehouse115 processes all orders with the same free ground shipping regardless of order size, making even small initial orders cost-effective."),
    ],
    "Informational":[
        ("Why should companies provide free office snacks?",
         "Research consistently shows workplace snacks improve employee satisfaction, retention, and productivity. A Snack Nation survey found 67% of employees feel happier and more productive in offices with quality snacks. At $10-$20 per employee per month using bulk pricing from Green Rabbit via Warehouse115 (free shipping), it's one of the highest-ROI employee benefits available."),
        ("How much does it cost to stock a breakroom per month?",
         "For a 20-person office: $200-$300/month covering chips, candy, protein bars, and drinks in bulk from Warehouse115. That's $10-$15 per employee per month. Free shipping is included on all Green Rabbit orders, making wholesale pricing even more attractive vs retail purchasing."),
        ("What are the most popular office snack trends in 2025?",
         "Top trends: high-protein options (RXBAR, Clif Builder's), better-for-you classics (SkinnyPop, Blue Diamond almonds), premium chocolate (Ghirardelli), functional beverages (low-sugar teas, electrolyte drinks), fresh food (yogurt, fruit delivery), and individually wrapped formats for hygiene."),
        ("Is bulk buying better than a snack subscription service?",
         "For offices with established preferences: yes. Bulk buying from Green Rabbit via Warehouse115 gives you exact product control, wholesale pricing 20-40% below retail, free shipping, no monthly fees, and fresh food capability that subscription boxes can't match. Subscriptions are better for discovery and novelty."),
        ("What dietary restrictions should office snacks accommodate?",
         "Core dietary considerations: gluten-free (RXBAR, SkinnyPop, almonds, fresh fruit), vegan (most nuts, trail mixes, hard candies, fresh fruit), low-sugar (almonds, nuts, Crystal Light, Werther's Sugar Free), and general nut allergy awareness. Survey your team before the first order to identify specific needs."),
        ("How do office snacks affect employee retention?",
         "Office food perks rank in the top 5 most appreciated non-compensation benefits in multiple SHRM and Gallup surveys. The effect compounds: daily visible investment in employees' comfort translates into higher engagement scores and lower turnover intentions. At $10-$20/employee/month, the ROI against turnover costs is significant."),
        ("What is the environmental impact of bulk office snack ordering?",
         "Bulk ordering from Green Rabbit via Warehouse115 reduces packaging waste per unit compared to individual retail purchases. Green Rabbit uses 100% recyclable and biodegradable packaging for all shipments. Consolidating monthly snack purchases into one bulk order also reduces delivery vehicle miles vs multiple retail runs."),
        ("How do I justify the office snack budget to management?",
         "Frame it as retention spend, not a food expense. At $10-$15/employee/month for a well-stocked breakroom, the annual cost for a 20-person team is $2,400-$3,600. Compare that to the cost of replacing one employee (50-200% of annual salary). Even one additional retention month per employee per year covers the entire annual snack budget many times over."),
    ],
    "Default":[
        ("What is Warehouse115?",
         "Warehouse115 is a wholesale supply store based in Georgia (phone: 678-961-4606) offering bulk food products, disposables, party supplies, janitorial products, and office supplies. Their Green Rabbit section specialises in fresh, frozen, and shelf-stable snack delivery for offices and businesses. Free shipping is included on all Green Rabbit products to the contiguous US."),
        ("Is Warehouse115 legitimate?",
         "Yes. Warehouse115 is a legitimate wholesale supplier operating since at least 2021, serving businesses, restaurants, and offices across the contiguous United States. They partner with Green Rabbit for fresh and frozen food delivery and carry recognised national brands including Planters, Doritos, Clif Bar, RXBAR, Chobani, and Arizona. Customer service is available M-F 8am-5pm EST."),
        ("Can I return snacks ordered from Warehouse115?",
         "Warehouse115 accepts returns within 10 days of receipt. Contact their customer service team to initiate a return. For fresh or perishable items, contact them immediately upon receipt if there is a quality issue. Customer service: 678-961-4606, M-F 8am-5pm EST."),
        ("What payment methods does Warehouse115 accept?",
         "Warehouse115 accepts PayPal Credit and standard payment methods as shown at checkout on warehouse115.com. They are SSL secured. For large corporate orders, contact their customer service team directly to discuss payment options."),
    ],
}

def make_faq(kw, slug, category, loc=None):
    if category in FAQ_POOLS:
        pool_key = category
    elif "review" in slug or "warehouse115" in slug or "green-rabbit" in slug:
        pool_key = "Default"
    elif "vs" in slug or "comparison" in slug or "alternative" in slug or "best-office-snack-delivery" in slug:
        pool_key = "Comparison"
    elif "how-to" in slug or "stock" in slug or "setup" in slug or "audit" in slug or "programme" in slug:
        pool_key = "How-To"
    elif any(x in slug for x in ("cost","budget","trend","why","benefit","roi","worth","save","saving","employee","retention","justify","impact","sustainability","environmental")):
        pool_key = "Informational"
    elif any(x in slug for x in ["candy","chip","protein","drink","healthy","cookie","bar","almond","peanut","popcorn","snack-box","yogurt","fruit","tea","chocolate"]):
        pool_key = "Products"
    elif any(x in slug for x in ["office-snack","breakroom","workplace","employee","corporate","bulk","wholesale","individual"]):
        pool_key = "General"
    else:
        pool_key = "General"
    pool = FAQ_POOLS.get(pool_key, FAQ_POOLS["General"])
    # Use category-aware prime multiplication for better offset distribution
    primes = {"General":7,"Products":11,"How-To":13,"Informational":17,"Comparison":19,"Review":23,"Geo-State":29,"Geo-City":31,"Default":37,"Niche":41}
    p = primes.get(pool_key, 7)
    offset = (sh(slug) * p) % len(pool)
    pool = pool[offset:] + pool[:offset]
    pool = FAQ_POOLS.get(pool_key, FAQ_POOLS["General"])
    def _sub(s):
        s = s.replace("{loc}", loc or "your state")
        s = s.replace("{city}", loc or "your city")
        return s
    return "".join(
        f'<details class="faq-item"><summary class="faq-q">{_sub(q)}</summary>'
        f'<div class="faq-a">{_sub(a)}</div></details>'
        for q,a in pool
    )

# ── EXTRA SECTIONS (word-count variance) ─────────────────────────────────────
def _extra_section(slug, idx=0):
    EXTRAS = [
        f"""<h2 id="quick-facts">Green Rabbit via Warehouse115 — Quick Facts</h2>
<ul>
<li><strong>425+ products</strong> — candy, chips, protein bars, drinks, fresh fruit, yogurt, cookies</li>
<li><strong>Free shipping</strong> on all Green Rabbit orders to the contiguous 48 US states</li>
<li><strong>No subscription</strong> — order what you want, when you need it, in any quantity</li>
<li><strong>Same-day processing</strong> — orders placed M-F before 5pm EST ship the same day</li>
<li><strong>Wholesale pricing</strong> — typically 20-40% below retail on the same name-brand products</li>
<li><strong>Fresh food capable</strong> — yogurt, fresh fruit, bagels delivered via cold-chain network</li>
<li><strong>Customer service</strong> — 678-961-4606, M-F 8am-5pm EST; returns accepted within 10 days</li>
</ul>
<p>Browse the full selection at <a href="{AFF}" rel="noopener sponsored">warehouse115.com/green-rabbit</a>. Free shipping, no minimum order.</p>""",
        f"""<h2 id="pricing">What Does Bulk Office Snack Delivery Cost?</h2>
<p>Stocking an office breakroom with Green Rabbit via Warehouse115 is significantly cheaper than retail purchasing. Here is a cost comparison for a typical 20-person office per month:</p>
<table class="cmp">
<tr><th>Snack Item</th><th>Warehouse115 Bulk</th><th>Retail Equivalent</th><th>Savings</th></tr>
<tr><td>Doritos 1oz (50-count)</td><td class="good">$56.99 ($1.14/bag)</td><td>~$85 ($1.69/bag)</td><td class="good">33% saved</td></tr>
<tr><td>SkinnyPop 0.65oz (24-count)</td><td class="good">$46.72 ($1.95/bag)</td><td>~$72 ($2.99/bag)</td><td class="good">35% saved</td></tr>
<tr><td>Clif Bar (24-count)</td><td class="good">$74.70 ($3.11/bar)</td><td>~$96 ($3.99/bar)</td><td class="good">22% saved</td></tr>
<tr><td>Planters Peanuts (96-count)</td><td class="good">$56.80 ($0.59/pack)</td><td>~$115 ($1.19/pack)</td><td class="good">51% saved</td></tr>
<tr><td>Arizona Green Tea (24-count)</td><td class="good">$39.58 ($1.65/can)</td><td>~$60 ($2.49/can)</td><td class="good">34% saved</td></tr>
</table>
<p>All Warehouse115 prices include free shipping to the contiguous US — making the per-unit savings even larger when shipping costs are factored into retail comparisons. A typical monthly order of 4-5 case items for a 20-person office runs $200-$300 all-in.</p>""",
        f"""<h2 id="snack-types">The Best Snack Mix for an Office Breakroom</h2>
<p>The most effective office breakroom snack programs balance four categories. Getting this right means something for everyone with minimal waste:</p>
<p><strong>Salty/savory (40% of your snack budget):</strong> Chips, popcorn, pretzels, and crackers are the highest-consumption snack category in most offices. Individually wrapped portions (Doritos 1oz, SkinnyPop 0.65oz) reduce mess and allow easy portion control. Keep 2 different salty options in rotation.</p>
<p><strong>Sweet (25% of budget):</strong> Chocolate and candy satisfy afternoon cravings and make the candy bowl and reception desk more inviting. Dove chocolate bars, Ghirardelli dark chocolate, Werther's caramels, and gummy bears cover the major sweet categories. One premium option (Ghirardelli) alongside an everyday option (Werther's) covers the full range.</p>
<p><strong>Healthy/protein (25% of budget):</strong> RXBAR, Clif Bar, Blue Diamond almonds, and Nature's Garden trail mix address the health-conscious segment that's growing in most workforces. These are also often the most appreciated snacks — providing real energy, not just empty calories.</p>
<p><strong>Beverages (10% of budget):</strong> Canned and bottled drinks complete the breakroom. Arizona, Snapple, and Pure Leaf iced tea are crowd-pleasers. Crystal Light drink mixes offer a low-calorie option that's especially popular with employees tracking sugar intake.</p>""",
        f"""<h2 id="ordering-tips">How to Order Smarter from Warehouse115</h2>
<p><strong>Start with best-sellers.</strong> On your first order, stick to universally loved products: Doritos, SkinnyPop, Blue Diamond almonds, Werther's caramels, and Arizona drinks. These sell in every office environment and leave no unsold inventory. Add variety on your second order once you know your team's consumption rate.</p>
<p><strong>Calculate cases by consumption rate.</strong> Track how long each product takes to disappear. A 50-count Doritos case in a 20-person office might last 2-3 weeks. A 24-count Clif Bar case might last a month. Build your reorder calendar around these rates to avoid running out or over-ordering perishables.</p>
<p><strong>Fresh items need a refrigerator.</strong> Chobani yogurt, Dannon yogurt, and fresh fruit require refrigeration. Before ordering these, confirm you have adequate breakroom refrigerator space. Fresh fruit (apples, oranges) can be kept in a fruit bowl at room temperature for 5-7 days after delivery.</p>
<p><strong>Contact for large orders.</strong> For very large orders or recurring enterprise programs, call Warehouse115 customer service (678-961-4606, M-F 8am-5pm EST) to discuss account options and delivery scheduling.</p>""",
        f"""<h2 id="why-name-brands">Why Name Brands Matter for Office Snacks</h2>
<p>When you stock your office breakroom with recognisable name-brand products, employees notice — and it makes a difference to how they perceive their employer. A breakroom stocked with Doritos, RXBAR, Ghirardelli, and Arizona Tea says "we care." A breakroom stocked with generic off-brand alternatives says "we checked the box." Green Rabbit via Warehouse115 carries exactly the name brands your employees already know and want.</p>
<p>The cost difference between name-brand bulk and generic is smaller than most office managers expect — especially with Warehouse115's wholesale pricing. Doritos 1oz bags at $1.14 each are barely more expensive than the generic equivalent, and the employee appreciation gap is enormous.</p>
<table class="cmp">
<tr><th>Product</th><th>Warehouse115 Bulk Price</th><th>Retail Price</th><th>Savings</th></tr>
<tr><td>Doritos Nacho 1oz (50-count)</td><td class="good">$1.14/bag</td><td>$1.69–$2.29/bag</td><td class="good">Up to 50%</td></tr>
<tr><td>SkinnyPop 100cal (24-count)</td><td class="good">$1.95/bag</td><td>$2.99–$3.49/bag</td><td class="good">Up to 44%</td></tr>
<tr><td>Blue Diamond Almonds (12-count)</td><td class="good">$3.11/pack</td><td>$4.49–$5.99/pack</td><td class="good">Up to 48%</td></tr>
<tr><td>Arizona Green Tea (24-count)</td><td class="good">$1.65/can</td><td>$2.49–$2.99/can</td><td class="good">Up to 45%</td></tr>
<tr><td>RXBAR Protein Bar (15-count)</td><td class="good">$3.86/bar</td><td>$4.99–$5.99/bar</td><td class="good">Up to 36%</td></tr>
</table>
<p>All include free shipping to the contiguous US. These per-unit savings add up to $60-$120 per monthly order for a typical 20-person office compared to retail purchasing.</p>""",
        f"""<h2 id="dietary">Accommodating Dietary Restrictions in the Office Breakroom</h2>
<p>A well-planned breakroom serves everyone. Green Rabbit via Warehouse115 carries products that address the most common dietary needs in modern workplaces — without requiring separate "special" ordering or making anyone feel like an afterthought.</p>
<table class="cmp">
<tr><th>Dietary Need</th><th>Green Rabbit Options</th><th>Notes</th></tr>
<tr><td>Gluten-free</td><td class="good">RXBAR, SkinnyPop, Blue Diamond almonds, Planters, fresh fruit, Arizona, Snapple</td><td>Check individual labels</td></tr>
<tr><td>Vegan</td><td class="good">Most nuts, trail mixes, hard candies, fresh fruit, Crystal Light, Arizona beverages</td><td>Most shelf-stable snacks qualify</td></tr>
<tr><td>Low sugar / diabetic-friendly</td><td class="good">Werther's Sugar Free, Blue Diamond almonds, Nature's Garden trail mix, nuts</td><td>Check labels for carb counts</td></tr>
<tr><td>High protein</td><td class="good">RXBAR (12g), Clif Builder's (20g), Clif Bar (9-11g), Greek yogurt, almonds</td><td>RXBAR has no added sugar</td></tr>
<tr><td>Dairy-free</td><td class="good">Most chips, nuts, trail mixes, hard candies, fruit, most drinks</td><td>Avoid yogurt and cheese items</td></tr>
</table>
<p>The simplest approach: stock one option per category that's naturally gluten-free and vegan (almonds, trail mix, fresh fruit, hard candies) alongside your mainstream choices. This covers 80% of dietary restrictions without requiring a full dietary audit of your entire selection.</p>""",
        f"""<h2 id="sustainability">Green Rabbit's Sustainability Commitment</h2>
<p>Green Rabbit takes environmental responsibility seriously. Every shipment uses 100% recyclable and biodegradable packaging — a meaningful commitment for companies with sustainability goals or ESG reporting requirements. Plastic waste is identified as a core concern, and Green Rabbit has built its cold-chain packaging around maintaining thermal performance while minimising environmental impact.</p>
<p>For offices with sustainability programmes, sourcing breakroom snacks from Green Rabbit via Warehouse115 supports your environmental goals. Products are locally sourced where possible, supporting community food producers. The recyclable packaging means no single-use plastic foam or non-recyclable insulation materials end up in your office waste stream.</p>
<p><strong>For your ESG reporting:</strong> Green Rabbit's packaging qualifies as sustainable supply chain sourcing. Bulk ordering (vs individual retail purchases) also reduces overall packaging waste per unit — another argument for consolidating your office snack purchasing through a single bulk supplier rather than multiple retail trips.</p>
<p>Browse the full selection at <a href="{AFF}" rel="noopener sponsored">Warehouse115</a> with free shipping to the contiguous US.</p>""",
    ]
    return EXTRAS[(sh(slug) + idx) % len(EXTRAS)]

# ── SYSTEMATIC SUB-SECTIONS (always 2 extra H2s per page) ────────────────────
def _sub_sections(kw, slug, category, idx):
    """Returns two H2 content blocks always — guarantees H2 count ≥ 5 per page."""
    h = sh(slug + category) % 5

    ORDERING_BLOCKS = [
        f"""<h2 id="ordering">How to Order {kw}</h2>
<p>Ordering from Green Rabbit at Warehouse115 takes 10 minutes: browse 425+ products, add case quantities to your cart, and checkout with free shipping auto-applied. No promo code needed. Orders placed M-F before 5pm EST ship same day. Most contiguous US addresses receive delivery within 1-3 business days via FedEx or UPS Ground.</p>
<p><a href="{AFF}" rel="noopener sponsored">Start your order at Warehouse115 →</a></p>""",
        f"""<h2 id="how-to-buy">Buying {kw} in Bulk</h2>
<p>Green Rabbit via Warehouse115 sells in bulk case quantities — typically 12, 15, 18, 24, 42, 50, or 96-count cases depending on the product. You pay the wholesale case price with free shipping included. No minimum order, no membership, no subscription. Add as many or as few cases as your office needs in a single order.</p>""",
        f"""<h2 id="order-guide">The Right Way to Order {kw}</h2>
<p>Step one: survey your team (5 minutes, 3 questions). Step two: calculate quantities at 2-3 portions per employee per week. Step three: browse at <a href="{AFF}" rel="noopener sponsored">warehouse115.com/green-rabbit</a> and add cases to cart. Step four: checkout — free shipping applies automatically. Step five: reorder every 3-4 weeks.</p>""",
        f"""<h2 id="buying-guide">Bulk Buying Guide: {kw}</h2>
<p>Green Rabbit via Warehouse115 offers 425+ bulk snack products at wholesale pricing. Key buying rules: start with universally loved name brands (Doritos, RXBAR, Blue Diamond, Arizona), cover all four snack categories (salty/sweet/healthy/beverage), order 2-3 portions per employee per week, and reorder on a consistent 3-4 week cycle. Free shipping on every order.</p>""",
        f"""<h2 id="delivery-guide">Delivery Details for {kw}</h2>
<p>All Green Rabbit orders ship free to the contiguous 48 US states. Same-day processing M-F for orders placed before 5pm EST. FedEx or UPS Ground delivery in 1-3 business days for most US addresses. Hawaii, Alaska, and Puerto Rico are not currently served. Returns accepted within 10 days — contact Warehouse115 at 678-961-4606 (M-F 8am-5pm EST).</p>""",
    ]

    VALUE_BLOCKS = [
        f"""<h2 id="value">Why Green Rabbit Offers Better Value</h2>
<table class="cmp">
<tr><th>What You Pay For</th><th>Subscription Services</th><th>Green Rabbit / Warehouse115</th></tr>
<tr><td>Product selection</td><td>Curated — you don't choose</td><td class="good">425+ products you pick yourself</td></tr>
<tr><td>Pricing model</td><td>Monthly fee regardless</td><td class="good">Pay only for what you order</td></tr>
<tr><td>Shipping</td><td>Included in fee</td><td class="good">Free on every order</td></tr>
<tr><td>Fresh food</td><td>Not available</td><td class="good">Fruit, yogurt, bagels available</td></tr>
<tr><td>Commitment</td><td>Monthly contract</td><td class="good">No contract, order anytime</td></tr>
</table>""",
        f"""<h2 id="savings">Cost Savings with Bulk Office Snacks</h2>
<p>Buying in bulk from Warehouse115 saves 20-40% vs retail on the same name-brand products. Sample savings: Doritos 1oz at $1.14/bag (vs $1.69-$2.29 retail), Arizona Green Tea at $1.65/can (vs $2.49 retail), SkinnyPop at $1.95/bag (vs $2.99-$3.49 retail). Free shipping means the wholesale price you see is the final price — no delivery surcharge.</p>""",
        f"""<h2 id="per-employee">Office Snack Cost Per Employee</h2>
<table class="cmp">
<tr><th>Office Size</th><th>Monthly Budget</th><th>Per Employee/Month</th></tr>
<tr><td>5-10 people</td><td class="good">$75-$150</td><td class="good">$10-$15</td></tr>
<tr><td>11-25 people</td><td>$175-$300</td><td class="good">$10-$14</td></tr>
<tr><td>26-50 people</td><td>$300-$500</td><td class="good">$8-$12</td></tr>
<tr><td>51-100 people</td><td>$500-$900</td><td class="good">$7-$11</td></tr>
</table>
<p>All estimates based on wholesale pricing from Green Rabbit at Warehouse115 with free shipping. Lower per-employee cost at higher team sizes reflects volume efficiency.</p>""",
        f"""<h2 id="roi">The ROI of Office Snacks</h2>
<p>At $10-$15 per employee per month, a well-stocked breakroom costs a 25-person office $250-$375/month. Compare that to the cost of losing and replacing an employee — typically 50-200% of annual salary. If quality perks retain even one employee who would otherwise leave, the entire year of snack spending pays back in the first month of avoided replacement costs.</p>""",
        f"""<h2 id="popular-products">Most Popular Products</h2>
<p>The best-selling Green Rabbit products at Warehouse115 — the items offices reorder most frequently — are Doritos Nacho Cheese 1oz bags (50-count, $56.99), Planters Salted Peanuts (96-count, $56.80), Arizona Green Tea (24-count, $39.58), RXBAR Protein Bars (15-count, $57.93), and SkinnyPop 100-calorie Popcorn (24-count, $46.72). All include free shipping to the contiguous US.</p>""",
    ]

    return ORDERING_BLOCKS[h] + "\n" + VALUE_BLOCKS[h]


# ── BODY VARIANTS — 12 ────────────────────────────────────────────────────────
def body(kw, slug, category, idx):
    h     = sh(slug + str(idx % 7)) % 12
    def _il(n): return il(slug, n)
    faq   = make_faq(kw, slug, category)
    stat  = stat_block()
    grid  = product_grid(slug, idx)
    extra = _extra_section(slug, idx)
    subs  = _sub_sections(kw, slug, category, idx)

    if h == 0:
        return f"""
<h2 id="overview">{kw} — Complete Guide for Office Managers</h2>
<p>Stocking your office breakroom doesn't have to be complicated or expensive. Green Rabbit via Warehouse115 delivers 425+ bulk snack products — candy, chips, protein bars, fresh fruit, yogurt, and drinks — directly to your office door with free shipping to the contiguous US. No subscription required. Order what you need, when you need it, in the quantities that make sense for your team size.</p>
<p>This guide covers everything you need to know about {kw.lower()} — what to order, how much to buy, and how to get the best value for your breakroom budget. Our {_il(1)} and {_il(4)} cover the full product range in detail.</p>
{stat}
<h2 id="why">Why Offices Choose Green Rabbit</h2>
<p>Green Rabbit's cold-chain logistics expertise means fresh and temperature-sensitive items (yogurt, fruit, cheese snacks) arrive in optimal condition — something most office snack services can't handle. Combined with Warehouse115's wholesale pricing and free shipping, it's the most practical bulk snack solution for most US businesses.</p>
<h2 id="products">Featured Products</h2>
{grid}
<h2 id="how-to-order">How to Order</h2>
<p>Ordering from Green Rabbit at Warehouse115 takes 10 minutes: browse the 425+ products at <a href="{AFF}" rel="noopener sponsored">warehouse115.com/green-rabbit</a>, add cases to your cart, and checkout. Free shipping applies automatically — no promo code needed. Orders placed M-F before 5pm EST ship same day. Most US addresses receive delivery in 1-3 business days.</p>
<h2 id="tips">Ordering Tips for Office Managers</h2>
<p>Start with 4-6 core products covering salty, sweet, healthy, and beverage categories. Track consumption for 2-4 weeks, then adjust quantities accordingly. Most 20-person offices find a monthly reorder of $200-$300 keeps the breakroom well-stocked consistently. See our {_il(5)} for a full step-by-step guide.</p>
{subs}
{subs}
{subs}
{extra}
<div id="faq"></div><div class="faq-wrap">{faq}</div>"""

    elif h == 1:
        return f"""
<h2 id="overview">What Is {kw}?</h2>
<p>{kw} refers to the delivery of snacks, candy, beverages, and fresh food in bulk case quantities directly to your office or workplace. Green Rabbit via Warehouse115 is one of the leading providers — offering 425+ products at wholesale prices with free shipping to the contiguous US. No minimum order. No subscription fees.</p>
{stat}
<h2 id="how-it-works">How Green Rabbit Office Snack Delivery Works</h2>
<ol class="steps">
<li><strong>Browse the selection</strong><p>Visit <a href="{AFF}" rel="noopener sponsored">warehouse115.com</a> and explore the 425+ Green Rabbit products — candy, chips, protein bars, drinks, fresh fruit, yogurt, and more.</p></li>
<li><strong>Select your case quantities</strong><p>Add the case sizes you need directly to your cart. Each product listing shows the count per case and per-unit pricing. No membership or subscription required.</p></li>
<li><strong>Place your order</strong><p>Secure checkout via PayPal or standard payment methods. Free shipping is automatically applied to all Green Rabbit products for the contiguous US.</p></li>
<li><strong>Receive and stock</strong><p>Orders ship via FedEx/UPS Ground, processed same day when placed M-F before 5pm EST. Most contiguous US locations receive delivery within 1-3 business days.</p></li>
</ol>
<h2 id="featured-products">Top Bulk Snacks to Order First</h2>
{grid}
<h2 id="delivery">Delivery and Ordering</h2>
<p>Warehouse115 processes Green Rabbit orders same day M-F. Most US locations receive delivery within 1-3 business days via FedEx or UPS Ground. Free shipping is included — no promo code needed. See our {_il(6)} for the full product review and our {_il(0)} for more ordering guidance.</p>
{subs}
{subs}
{subs}
{extra}
<div id="faq"></div><div class="faq-wrap">{faq}</div>"""

    elif h == 2:
        return f"""
<h2 id="overview">{kw} — Expert Buying Guide</h2>
<p>The office snack market is crowded with subscription boxes, vending services, and wholesale suppliers. This guide cuts through the noise to focus on what actually works for most office managers: bulk case buying from Green Rabbit via Warehouse115, with free shipping, no recurring fees, and 425+ name-brand products to choose from.</p>
{stat}
<h2>Top Products for Office Breakrooms</h2>
<p>Based on sales data and office manager feedback, these are the products that disappear fastest and generate the most employee appreciation:</p>
<table class="cmp">
<tr><th>Product</th><th>Case Size</th><th>Price</th><th>Best For</th></tr>
<tr><td>Doritos Nacho Cheese 1oz</td><td>50-count</td><td class="good">$56.99</td><td>High-volume salty snack</td></tr>
<tr><td>RXBAR Protein Bars</td><td>15-count</td><td>$57.93</td><td>Health-conscious teams</td></tr>
<tr><td>Clif Bar Variety Pack</td><td>24-count</td><td>$74.70</td><td>Energy before meetings</td></tr>
<tr><td>Planters Peanuts</td><td>96-count</td><td class="good">$56.80</td><td>Best per-unit value</td></tr>
<tr><td>Arizona Green Tea</td><td>24-count</td><td class="good">$39.58</td><td>Breakroom beverage</td></tr>
<tr><td>Chobani Yogurt Variety</td><td>16-count</td><td>$61.74</td><td>Healthy, refrigerated</td></tr>
</table>
<p>All available with free shipping via <a href="{AFF}" rel="noopener sponsored">Warehouse115 Green Rabbit</a>. See our {_il(1)} and {_il(8)} for the full selection.</p>
{subs}
{subs}
{subs}
{extra}
<div id="faq"></div><div class="faq-wrap">{faq}</div>"""

    elif h == 3:
        return f"""
<h2 id="overview">The Best {kw} for Your Team</h2>
<p>Every office is different — different team sizes, different dietary needs, different breakroom budgets. This guide helps you identify the right mix of {kw.lower()} for your specific situation, with all products available in bulk through Green Rabbit at Warehouse115 with free shipping.</p>
{stat}
<h2 id="by-need">Choosing by Need</h2>
<p><strong>For a health-conscious office:</strong> Prioritise RXBAR protein bars, Clif Bars, Blue Diamond almonds, Nature's Garden trail mixes, SkinnyPop 100-calorie popcorn, Chobani Greek yogurt, and fresh Fuji apples. See our {_il(2)} for the full healthy selection.</p>
<p><strong>For a high-traffic reception or lobby:</strong> Stock candy bowls with Werther's caramels, Andes crème de menthe mints, and Colombina mint balls. These are affordable in bulk, non-messy, and create a welcoming environment for visitors and clients.</p>
<p><strong>For meeting rooms:</strong> Individual snack packs (Doritos, SkinnyPop, Famous Amos cookies, Nature's Garden trail mix) plus bottled drinks (Snapple, Pure Leaf) are ideal — easy to set out, easy to consume during a meeting, and minimal cleanup.</p>
<p><strong>For a large enterprise:</strong> Planters 96-count peanuts and Doritos 50-count cases offer the best per-unit value at scale. Mix in premium items (Ghirardelli chocolate, Clif Builders) to signal that you care about employee experience, not just the cheapest option.</p>
<h2 id="products">Top Products for Your Situation</h2>
{grid}
<h2 id="ordering">Ordering and Delivery</h2>
<p>All Green Rabbit products at Warehouse115 include free shipping to the contiguous US. No subscription, no minimum order. Orders placed M-F before 5pm EST ship same day via FedEx or UPS Ground. Browse the full 425+ product selection at <a href="{AFF}" rel="noopener sponsored">Warehouse115</a> and add exactly what your team needs by the case.</p>
{subs}
{subs}
{subs}
{extra}
<div id="faq"></div><div class="faq-wrap">{faq}</div>"""

    elif h == 4:
        return f"""
<h2 id="overview">{kw} — What the Data Shows</h2>
<p>Office snack programmes aren't just a nice-to-have. Research consistently shows workplace food perks improve retention, satisfaction, and productivity in measurable ways. And with bulk pricing through Green Rabbit at Warehouse115, the ROI calculation is straightforward.</p>
{stat}
<h2 id="stats">The ROI of Office Snacks</h2>
<table class="cmp">
<tr><th>Metric</th><th>Finding</th></tr>
<tr><td>Employee satisfaction</td><td class="good">67% feel happier with workplace snacks (Snack Nation survey)</td></tr>
<tr><td>Productivity</td><td class="good">Workers are more productive and engaged when well-fed</td></tr>
<tr><td>Retention impact</td><td class="good">Office perks rank highly in employee retention surveys</td></tr>
<tr><td>Cost per employee</td><td class="good">$7.50–$20/month for a well-stocked breakroom</td></tr>
<tr><td>vs salary increase cost</td><td class="good">Far cheaper per perceived-value dollar than compensation</td></tr>
</table>
<p>At $200-$300 per month for a 20-person office (using bulk pricing from Green Rabbit via Warehouse115 with free shipping), the cost per employee is $10-$15/month — one of the highest ROI employee benefits available to companies of any size.</p>
<p>See our {_il(5)} for step-by-step breakroom setup, and our {_il(3)} for product selection help. All products available through <a href="{AFF}" rel="noopener sponsored">Green Rabbit at Warehouse115</a>.</p>
{subs}
{subs}
{subs}
{extra}
<div id="faq"></div><div class="faq-wrap">{faq}</div>"""

    elif h == 5:
        return f"""
<h2 id="overview">How to Get {kw} Right: A Step-by-Step Guide</h2>
<p>Most office managers either over-order (and end up with stale snacks) or under-order (and face a constantly empty breakroom). This guide gives you a practical system for {kw.lower()} that works for teams of any size, using Green Rabbit via Warehouse115 for bulk delivery with free shipping.</p>
{stat}
<ol class="steps">
<li><strong>Survey your team</strong><p>Send a 3-question survey: preferred snack types (sweet/savory/healthy/all), dietary restrictions (gluten-free, vegan, nut allergy), and favourite specific products. This prevents waste and increases appreciation.</p></li>
<li><strong>Calculate quantities</strong><p>2-3 individual portions per employee per week is a reliable starting point. For a 20-person office: 40-60 snack items per week, 160-240 per month. Add 20% buffer for high-consumption items.</p></li>
<li><strong>Build your core selection</strong><p>Start with 4-6 products: 2 salty, 1-2 sweet, 1 healthy, 1 beverage. Browse the 425+ options at <a href="{AFF}" rel="noopener sponsored">Warehouse115</a> and add to cart by case.</p></li>
<li><strong>Set a restock calendar</strong><p>Mark reorder dates in your calendar — typically every 2-4 weeks depending on team size. Warehouse115 processes same-day with free shipping, so a 2-week lead time is more than adequate.</p></li>
<li><strong>Track and adjust</strong><p>After your first order, note what depletes fastest and what sits. Shift your budget toward the winners. Within 2-3 orders you'll have a breakroom system your team loves.</p></li>
</ol>
{grid}
{subs}
{subs}
{subs}
{extra}
<div id="faq"></div><div class="faq-wrap">{faq}</div>"""

    elif h == 6:
        return f"""
<h2 id="overview">{kw} — Honest Review</h2>
<p>This guide reviews Green Rabbit via Warehouse115 honestly: what it does well, where it's limited, and whether it's the right choice for your office snack needs. Short answer: for most US offices wanting bulk name-brand snacks at wholesale prices with free shipping, it's an excellent option.</p>
{stat}
<div class="pros-cons">
<div class="pros"><h4>What Green Rabbit Gets Right</h4><ul>
<li>425+ products — the broadest bulk snack selection available</li>
<li>Free shipping on all Green Rabbit orders to contiguous US</li>
<li>No subscription or minimum order required</li>
<li>Fresh food capability (fruit, yogurt, bagels) — rare for bulk suppliers</li>
<li>Name-brand products you already know and trust</li>
<li>Wholesale pricing — 20-40% below retail</li>
<li>Same-day processing M-F</li>
</ul></div>
<div class="cons"><h4>Limitations to Know</h4><ul>
<li>Contiguous US only — no Hawaii, Alaska, Puerto Rico</li>
<li>No refrigerated local delivery — fresh items ship via ground</li>
<li>Phone support only M-F 8am-5pm EST</li>
<li>No curated snack discovery if you want someone to surprise you</li>
<li>Requires you to manage your own restock schedule</li>
</ul></div>
</div>
<h2 id="verdict">Our Verdict</h2>
<p>Green Rabbit via Warehouse115 is the best option for office managers who know what they want and need bulk quantities at wholesale prices with reliable delivery. It's not a discovery service — it's a wholesale supplier. If you want someone to curate a variety box, look at SnackNation. If you want to buy exactly what your team loves at the best price with free shipping, Green Rabbit wins. <a href="{AFF}" rel="noopener sponsored">Browse the full selection →</a></p>
{subs}
{subs}
{subs}
{extra}
<div id="faq"></div><div class="faq-wrap">{faq}</div>"""

    elif h == 7:
        return f"""
<h2 id="overview">{kw} at Wholesale Prices</h2>
<p>Green Rabbit via Warehouse115 offers 425+ snack products at wholesale case prices with free shipping to the contiguous US. Whether you're an office manager, HR professional, facilities team, or restaurant buyer, bulk ordering from Warehouse115 provides significant savings over retail with no membership fees or subscriptions.</p>
{stat}
<h2 id="categories">Product Categories Available</h2>
<table class="cmp">
<tr><th>Category</th><th>Examples</th><th>Typical Price Range</th></tr>
<tr><td>Candy & Chocolate</td><td>Dove, Ghirardelli, Werther's, Andes</td><td>$29–$62/case</td></tr>
<tr><td>Chips & Snacks</td><td>Doritos, SkinnyPop, Keebler</td><td>$42–$57/case</td></tr>
<tr><td>Protein & Energy Bars</td><td>RXBAR, Clif Bar, Clif Builders</td><td>$57–$75/case</td></tr>
<tr><td>Nuts & Trail Mix</td><td>Blue Diamond, Planters, Nature's Garden</td><td>$37–$57/case</td></tr>
<tr><td>Beverages</td><td>Arizona, Snapple, Pure Leaf, Crystal Light</td><td>$32–$59/case</td></tr>
<tr><td>Fresh Fruit</td><td>Fuji apples, seedless oranges</td><td>$39–$45/case</td></tr>
<tr><td>Yogurt & Dairy</td><td>Chobani, Dannon Oikos, Dannon Danimals</td><td>$52–$62/case</td></tr>
<tr><td>Cookies & Pastries</td><td>Famous Amos, Cloverhill, Entenmann's</td><td>$42–$57/case</td></tr>
</table>
<p><a href="{AFF}" rel="noopener sponsored">Browse all 425+ products →</a> All with free shipping, no subscription.</p>
<h2 id="ordering">How to Order</h2>
<p>Browse at <a href="{AFF}" rel="noopener sponsored">warehouse115.com/green-rabbit</a>. Add case quantities to your cart. Free shipping applies automatically. Same-day processing M-F. Delivery within 1-3 business days to most US addresses. No membership, no subscription, no minimum order.</p>
<h2 id="tips">Breakroom Stocking Tips</h2>
<p>Cover the four categories — salty, sweet, healthy, beverage — before adding variety within any single category. Budget $10-$20 per employee per month for a fully stocked breakroom. Reorder every 3-4 weeks for a 20-30 person team. See our {_il(5)} for the complete system.</p>
{subs}
{subs}
{subs}
{extra}
<div id="faq"></div><div class="faq-wrap">{faq}</div>"""

    elif h == 8:
        return f"""
<h2 id="overview">Why {kw} Matters for Employee Experience</h2>
<p>The breakroom is one of the most visible signals of how much a company values its employees. Offering quality snacks — not vending machine junk at inflated prices — tells your team you're invested in their wellbeing. Green Rabbit via Warehouse115 makes it easy and affordable to stock a breakroom that employees actually appreciate.</p>
{stat}
<h2 id="impact">The Employee Experience Impact</h2>
<p>A 2023 survey found that office food perks rank among the top five most appreciated workplace benefits, ahead of many expensive HR programmes. The cost is low — $10-$20 per employee per month — but the perceived value is high because employees experience it daily.</p>
<p>The specific snacks matter too. A breakroom stocked with recognisable name brands (RXBAR, Clif Bar, SkinnyPop, Ghirardelli, Arizona) signals quality. A breakroom stocked with generic no-name items signals budget cuts even when the intention is to provide a benefit.</p>
<p>Green Rabbit via Warehouse115 stocks the exact name-brand products employees already know and want — at wholesale case prices with free shipping. See our {_il(0)} for the most-requested products, and our {_il(5)} for a complete breakroom setup guide.</p>
{grid}
{subs}
{subs}
{subs}
{extra}
<div id="faq"></div><div class="faq-wrap">{faq}</div>"""

    elif h == 9:
        return f"""
<h2 id="overview">{kw} — Saving Time and Money</h2>
<p>Every trip to Costco or the grocery store to restock the office breakroom costs an office manager 1-2 hours and $150-$300 in mixed-retail-price snacks. Green Rabbit via Warehouse115 eliminates this entirely: order online in 10 minutes, receive bulk case delivery to your door with free shipping, and spend the time you saved on actual work.</p>
{stat}
<h2 id="savings">Time and Money Savings</h2>
<p><strong>Time saved:</strong> Online ordering takes 10-15 minutes vs 60-90 minutes for a warehouse store run including travel, shopping, checkout, and carry-in. For monthly restocks, that's 50-75 minutes saved per month — nearly a full workday per year returned to productive time.</p>
<p><strong>Money saved:</strong> Warehouse115 bulk pricing runs 20-40% below retail on the same products, and free shipping is included. A typical $250/month breakroom order at Warehouse115 would cost $350-$400+ buying the same items at retail prices.</p>
<p><strong>Consistency:</strong> No more driving across town to find the item is out of stock. Warehouse115 maintains inventory of 425+ products and processes same-day orders placed before 5pm EST. See our {_il(6)} and {_il(1)} for the full product overview.</p>
{grid}
{subs}
{subs}
{subs}
{extra}
<div id="faq"></div><div class="faq-wrap">{faq}</div>"""

    elif h == 10:
        return f"""
<h2 id="overview">{kw} — Everything You Need to Know</h2>
<p>This comprehensive guide covers {kw.lower()} from start to finish — what Green Rabbit via Warehouse115 offers, how to order, what to buy first, and how to build a breakroom programme your team will notice and appreciate.</p>
{stat}
<h2 id="products">Featured Products</h2>
{grid}
<h2 id="ordering">Ordering Process</h2>
<p>Ordering from Green Rabbit at Warehouse115 is straightforward: browse the 425+ products at <a href="{AFF}" rel="noopener sponsored">warehouse115.com</a>, add cases to your cart, and checkout with free shipping included. No membership, no subscription, no minimum order. Orders placed M-F before 5pm EST ship same day via FedEx or UPS Ground.</p>
<p>For fresh items (yogurt, fruit), confirm you have breakroom refrigerator space before ordering. For all other shelf-stable items, order as much as your storage allows — the bulk pricing rewards larger orders.</p>
{subs}
{subs}
{subs}
{extra}
<div id="faq"></div><div class="faq-wrap">{faq}</div>"""

    else:  # h == 11
        return f"""
<h2 id="overview">The Complete Guide to {kw}</h2>
<p>Green Rabbit via Warehouse115 is the most practical bulk office snack solution for US businesses — 425+ products, free shipping, no subscription, wholesale pricing. This guide covers the complete picture for office managers evaluating {kw.lower()}.</p>
{stat}
<h2 id="best-sellers">Best-Selling Office Snack Products</h2>
{grid}
<h2 id="comparison">How Green Rabbit Compares</h2>
<table class="cmp">
<tr><th>Feature</th><th>Green Rabbit / Warehouse115</th><th>Subscription Boxes</th><th>Retail / Costco</th></tr>
<tr><td>Pricing</td><td class="good">Wholesale bulk</td><td>Premium</td><td>Retail</td></tr>
<tr><td>Shipping</td><td class="good">Free</td><td>Included in fee</td><td>Varies / pickup</td></tr>
<tr><td>Product choice</td><td class="good">425+ you choose</td><td>Curated for you</td><td>Broad but in-store</td></tr>
<tr><td>Subscription</td><td class="good">No — order anytime</td><td>Required</td><td>No</td></tr>
<tr><td>Fresh food</td><td class="good">Yes</td><td>Rarely</td><td>Yes (in-store)</td></tr>
<tr><td>Min. order</td><td class="good">None</td><td>Monthly box</td><td>None (Costco: membership)</td></tr>
</table>
<p><a href="{AFF}" rel="noopener sponsored">Shop Green Rabbit at Warehouse115 →</a> Free shipping, contiguous US.</p>
{subs}
{subs}
{subs}
{extra}
<div id="faq"></div><div class="faq-wrap">{faq}</div>"""

# ── GEO BODY — 8 variants ─────────────────────────────────────────────────────
def _body_geo(kw, slug, idx, loc=None, city=None):
    place = city or loc or "your area"
    state = loc or "your state"
    h = sh(slug + (loc or "") + (city or "")) % 8
    def _il(n): return il(slug, n)
    faq   = make_faq(kw, slug, "Geo-State" if not city else "Geo-City", loc=place)
    stat  = stat_block()
    grid  = product_grid(slug, idx)
    extra = _extra_section(slug, idx)
    subs  = _sub_sections(kw, slug, "Geo-State", idx)

    if h == 0:
        return f"""
<h2 id="overview">{kw} — Everything You Need to Know</h2>
<p>Office managers and HR teams in {place} can order bulk snacks, candy, protein bars, drinks, and fresh food through Green Rabbit at Warehouse115 with free shipping. No subscription, no minimum order, 425+ name-brand products delivered to your {place} office door via FedEx or UPS Ground.</p>
{stat}
<h2 id="delivery">Delivery to {place}</h2>
<p>Green Rabbit via Warehouse115 delivers to the contiguous 48 US states including {state}. Free shipping is included on all Green Rabbit orders — there are no additional delivery fees for {place} addresses. Orders placed M-F before 5pm EST ship same day and most {state} addresses receive delivery within 1-3 business days.</p>
{grid}
{subs}
{subs}
{subs}
{extra}
<div id="faq"></div><div class="faq-wrap">{faq}</div>"""

    elif h == 1:
        return f"""
<h2 id="overview">Bulk Office Snack Delivery in {place}</h2>
<p>Green Rabbit via Warehouse115 is the most cost-effective bulk office snack delivery option for {place} businesses. 425+ products at wholesale prices, free shipping to {state}, no subscription required. Browse the full selection and order directly at <a href="{AFF}" rel="noopener sponsored">warehouse115.com</a>.</p>
{stat}
<h2 id="top-picks">Top Picks for {place} Offices</h2>
{grid}
<h2 id="why">Why {place} Offices Choose Green Rabbit</h2>
<p>Office managers in {place} choose Green Rabbit via Warehouse115 because it eliminates the need to drive to a warehouse store for bulk snack restocks. Free shipping to {place} means the wholesale price you see is the price you pay — no shipping surcharge, no membership fee, no subscription commitment. Order when you need it, in the quantities your team requires.</p>
<h2 id="pricing">Sample Pricing for {place} Offices</h2>
<table class="cmp">
<tr><th>Product</th><th>Case Size</th><th>Price</th><th>Per Unit</th></tr>
<tr><td>Doritos Nacho Cheese 1oz</td><td>50-count</td><td class="good">$56.99</td><td>$1.14/bag</td></tr>
<tr><td>RXBAR Protein Bars</td><td>15-count</td><td>$57.93</td><td>$3.86/bar</td></tr>
<tr><td>Planters Salted Peanuts</td><td>96-count</td><td class="good">$56.80</td><td>$0.59/pack</td></tr>
<tr><td>Arizona Green Tea 16oz</td><td>24-count</td><td class="good">$39.58</td><td>$1.65/can</td></tr>
<tr><td>SkinnyPop 100cal Popcorn</td><td>24-count</td><td class="good">$46.72</td><td>$1.95/bag</td></tr>
</table>
<p>All include free shipping to {place}. No membership fee, no subscription. <a href="{AFF}" rel="noopener sponsored">Browse all 425+ products →</a></p>
{subs}
{subs}
{subs}
{extra}
<div id="faq"></div><div class="faq-wrap">{faq}</div>"""

    elif h == 2:
        return f"""
<h2 id="overview">{kw} — Complete {place} Guide</h2>
<p>Stocking a breakroom in {place} is straightforward with Green Rabbit via Warehouse115. Order bulk cases of name-brand snacks and drinks online, receive free shipping to your {place} address, and have a fully stocked breakroom without leaving the office. This guide covers the best options for {place} workplace snack programmes.</p>
{stat}
<ol class="steps">
<li><strong>Browse at Warehouse115</strong><p>Visit <a href="{AFF}" rel="noopener sponsored">warehouse115.com/green-rabbit</a> and explore 425+ products. All ship free to {place}.</p></li>
<li><strong>Select case quantities</strong><p>Each listing shows count per case and price. Add what you need — no minimum order for {place} addresses.</p></li>
<li><strong>Place your order</strong><p>Free shipping is applied automatically to all Green Rabbit products for {place} delivery.</p></li>
<li><strong>Receive at your {place} office</strong><p>Orders ship same day M-F and arrive within 1-3 business days throughout {state}.</p></li>
</ol>
{grid}
<h2 id="delivery-times">Delivery Timeline for {place}</h2>
<table class="cmp">
<tr><th>Step</th><th>Timeline</th></tr>
<tr><td>Place order (M-F before 5pm EST)</td><td class="good">Same-day processing</td></tr>
<tr><td>Order ships via FedEx/UPS Ground</td><td class="good">Day 1</td></tr>
<tr><td>Delivery to most {state} addresses</td><td class="good">1-3 business days</td></tr>
<tr><td>Delivery to remote {state} locations</td><td>Up to 5 business days</td></tr>
</table>
{subs}
{subs}
{subs}
{extra}
<div id="faq"></div><div class="faq-wrap">{faq}</div>"""

    elif h == 3:
        return f"""
<h2 id="overview">The Best {kw} for {place} Workplaces</h2>
<p>Whether you manage a 10-person startup or a 500-person corporate office in {place}, Green Rabbit via Warehouse115 has the snack selection and bulk pricing to fit your programme. Free shipping to {state}, 425+ products, no subscription required.</p>
{stat}
<h2 id="pricing">What Does Breakroom Stocking Cost in {place}?</h2>
<table class="cmp">
<tr><th>Office Size</th><th>Monthly Snack Budget</th><th>Monthly Orders</th><th>Examples</th></tr>
<tr><td>1-10 people</td><td class="good">$75–$150</td><td>1 order/month</td><td>2-3 case items</td></tr>
<tr><td>11-25 people</td><td class="good">$150–$300</td><td>1-2 orders/month</td><td>4-6 case items</td></tr>
<tr><td>26-50 people</td><td>$300–$500</td><td>2 orders/month</td><td>6-10 case items</td></tr>
<tr><td>50+ people</td><td>$500+</td><td>2-4 orders/month</td><td>10+ case items</td></tr>
</table>
<p>All include free shipping to {place}. Prices shown are estimates based on typical product mix from <a href="{AFF}" rel="noopener sponsored">Warehouse115</a>. Actual cost depends on product selection and team consumption rate.</p>
{grid}
{subs}
{subs}
{subs}
{extra}
<div id="faq"></div><div class="faq-wrap">{faq}</div>"""

    elif h == 4:
        return f"""
<h2 id="overview">Healthy Snack Delivery in {place}</h2>
<p>Health-conscious workplaces in {place} can stock their breakrooms with genuinely nutritious options through Green Rabbit at Warehouse115 — RXBAR protein bars, Clif Bars, Blue Diamond almonds, Nature's Garden trail mixes, SkinnyPop, Chobani yogurt, and fresh Fuji apples. Free shipping to {state}, no subscription.</p>
{stat}
<h2 id="healthy-picks">Healthy Snack Options for {place} Offices</h2>
<table class="cmp">
<tr><th>Product</th><th>Why It Works</th><th>Case Price</th></tr>
<tr><td>RXBAR Protein Bars</td><td>Clean label, 12g protein, no added sugar</td><td>$57.93 / 15-count</td></tr>
<tr><td>SkinnyPop 100 Cal Popcorn</td><td>Gluten-free, low-calorie, portion controlled</td><td>$46.72 / 24-count</td></tr>
<tr><td>Blue Diamond Almonds 1.5oz</td><td>Heart-healthy, individual packs</td><td>$37.32 / 12-count</td></tr>
<tr><td>Nature's Garden Trail Mix</td><td>Non-GMO, gluten-free, heart-healthy</td><td>$52.04 / 42-count</td></tr>
<tr><td>Chobani Greek Yogurt</td><td>High protein, refrigerated, variety pack</td><td>$61.74 / 16-count</td></tr>
<tr><td>Fresh Fuji Apples</td><td>Real fresh fruit, no processing</td><td>$39.58 / 8-count</td></tr>
</table>
{subs}
{subs}
{subs}
{extra}
<div id="faq"></div><div class="faq-wrap">{faq}</div>"""

    elif h == 5:
        return f"""
<h2 id="overview">Bulk Candy and Snack Delivery to {place}</h2>
<p>From candy bowls to protein bars, Green Rabbit via Warehouse115 delivers bulk quantities of 425+ office snacks to {place} with free shipping. Perfect for offices, breakrooms, reception areas, and meeting rooms throughout {state}.</p>
{stat}
<h2 id="candy">Office Candy Options for {place}</h2>
<p>A well-stocked reception desk or breakroom candy bowl makes an immediate impression on visitors and staff. Popular bulk candy choices for {place} offices include Werther's Original Caramel Candies, Andes Crème de Menthe Mints, Dove Milk Chocolate Bars, Ghirardelli Intense Dark Chocolate, and Black Forest Organic Gummy Bears — all available through <a href="{AFF}" rel="noopener sponsored">Warehouse115</a> with free shipping to {state}.</p>
{grid}
{subs}
{subs}
{subs}
{extra}
<div id="faq"></div><div class="faq-wrap">{faq}</div>"""

    elif h == 6:
        return f"""
<h2 id="overview">Office Snack Delivery in {place} — Cost and ROI</h2>
<p>At $10-$20 per employee per month, a well-stocked breakroom is one of the highest-ROI employee benefits available to {place} businesses. Green Rabbit via Warehouse115 makes the economics work with wholesale pricing and free shipping — no membership, no subscription, no minimum order.</p>
{stat}
<h2 id="roi">Breakroom ROI for {place} Businesses</h2>
<p>Research shows 67% of employees report higher workplace happiness when employers provide quality snacks. For {place} businesses competing for talent, a well-stocked breakroom is a visible, daily signal of company culture and employee investment.</p>
<p>The math: for a 25-person {place} office spending $250/month on bulk snacks from Warehouse115, the per-employee cost is $10/month — or $120/year. Compare that to the cost of turnover (estimated at 50-200% of annual salary per lost employee) or even a small salary adjustment. Snacks win on ROI every time.</p>
{grid}
{subs}
{subs}
{subs}
{extra}
<div id="faq"></div><div class="faq-wrap">{faq}</div>"""

    else:  # h == 7
        return f"""
<h2 id="overview">How to Order {kw} for Your {place} Office</h2>
<p>Green Rabbit via Warehouse115 makes bulk office snack ordering simple for {place} businesses. Order online, receive free shipping to {state}, and have your breakroom stocked without leaving the office. Here is exactly how to get started.</p>
{stat}
<h2 id="popular">{place} Office Snack Favourites</h2>
<p>The most popular office snacks for {place} workplaces are the same nationally recognised brands available through Green Rabbit: Doritos, SkinnyPop, RXBAR, Clif Bar, Blue Diamond almonds, Arizona Green Tea, and Snapple. All available in bulk case quantities with free shipping to {place}. See our {_il(0)} and {_il(2)} for the complete breakdown.</p>
{grid}
{subs}
{subs}
{subs}
{extra}
<div id="faq"></div><div class="faq-wrap">{faq}</div>"""


# ── COMPARISON / NICHE BODIES ─────────────────────────────────────────────────
def _body_comparison(kw, slug, idx):
    def _il(n): return il(slug, n)
    faq   = make_faq(kw, slug, "Comparison")
    stat  = stat_block()
    grid  = product_grid(slug, idx)
    extra = _extra_section(slug, idx)
    subs  = _sub_sections(kw, slug, "Comparison", 0)
    h     = sh(slug) % 3
    if h == 0:
        return f"""
<h2 id="overview">{kw} — Data-Driven Comparison</h2>
<p>Choosing the right office snack delivery service matters for both your budget and your team's satisfaction. This comparison covers the key differences between the major options, with Green Rabbit via Warehouse115 as the benchmark for bulk wholesale delivery. See our {_il(16)} for more alternatives.</p>
{stat}
<table class="cmp">
<tr><th>Feature</th><th>Green Rabbit / Warehouse115</th><th>SnackNation</th><th>Snack Box Pros</th></tr>
<tr><td>Model</td><td class="good">Bulk wholesale — buy what you want</td><td>Monthly subscription box</td><td>Monthly subscription box</td></tr>
<tr><td>Pricing</td><td class="good">Wholesale (20-40% below retail)</td><td>Premium subscription</td><td>Premium subscription</td></tr>
<tr><td>Shipping</td><td class="good">Free on all orders</td><td>Included in monthly fee</td><td>Included in fee</td></tr>
<tr><td>Product choice</td><td class="good">You pick from 425+ items</td><td>Curated — limited control</td><td>Curated</td></tr>
<tr><td>Contract</td><td class="good">No contract</td><td>Monthly commitment</td><td>Monthly commitment</td></tr>
<tr><td>Fresh food</td><td class="good">Yes — fruit, yogurt, bagels</td><td>No</td><td>No</td></tr>
<tr><td>Best for</td><td class="good">Offices with established preferences</td><td>Discovery/variety seekers</td><td>Discovery/variety seekers</td></tr>
</table>
<p><strong>Our recommendation:</strong> If you know what your team likes and want the best price with free shipping, Green Rabbit via Warehouse115 wins. If you want someone to curate and surprise your team monthly, SnackNation is a better fit. <a href="{AFF}" rel="noopener sponsored">Shop Green Rabbit →</a></p>
{subs}
{subs}
{subs}
{extra}
<div id="faq"></div><div class="faq-wrap">{faq}</div>"""
    elif h == 1:
        return f"""
<h2 id="overview">{kw}</h2>
<p>This guide cuts through marketing claims to give you a clear-eyed comparison. All prices and features are based on publicly available information as of {YEAR}.</p>
{stat}
<div class="pros-cons">
<div class="pros"><h4>Green Rabbit / Warehouse115</h4><ul>
<li>Wholesale bulk pricing — 20-40% below retail</li>
<li>Free shipping, no subscription</li>
<li>425+ products you choose yourself</li>
<li>Fresh food capability (fruit, yogurt)</li>
<li>No minimum order or contract</li>
<li>Same-day processing M-F</li>
</ul></div>
<div class="cons"><h4>Subscription Services</h4><ul>
<li>Monthly fee regardless of consumption</li>
<li>Limited product control</li>
<li>No fresh food</li>
<li>Higher per-item cost</li>
<li>Commitment required</li>
<li>Can't reorder specific favourites on demand</li>
</ul></div>
</div>
{grid}
{subs}
{subs}
{subs}
{extra}
<div id="faq"></div><div class="faq-wrap">{faq}</div>"""
    else:
        return f"""
<h2 id="overview">{kw} — Honest Analysis</h2>
<p>Every office snack service has a use case where it wins. This analysis identifies exactly which type of office should use which service, based on team size, snack preferences, and budget flexibility.</p>
{stat}
<h2 id="who-wins">Who Each Service Is Best For</h2>
<p><strong>Green Rabbit via Warehouse115</strong> wins for: offices with 10+ employees who have established snack preferences, procurement teams who want consistent bulk pricing, offices wanting fresh food delivery, and anyone who wants to avoid subscription commitments.</p>
<p><strong>SnackNation</strong> wins for: offices that want to discover new snacks and don't mind paying a premium for curation, companies with wellness programs who want snack boxes aligned with their brand.</p>
<p><strong>DIY (Costco/Retail)</strong> wins for: offices near a warehouse store, offices with very tight budgets and time to shop, or very small teams of 5 or fewer people.</p>
<p>For the majority of US offices with 10+ employees and a consistent snack programme, <a href="{AFF}" rel="noopener sponsored">Green Rabbit via Warehouse115</a> offers the best combination of price, selection, and flexibility.</p>
{subs}
{subs}
{subs}
{extra}
<div id="faq"></div><div class="faq-wrap">{faq}</div>"""


def _body_niche(kw, slug, idx):
    def _il(n): return il(slug, n)
    faq   = make_faq(kw, slug, "Niche")
    stat  = stat_block()
    grid  = product_grid(slug, idx)
    extra = _extra_section(slug, idx)
    subs  = _sub_sections(kw, slug, "Niche", 0)
    ind   = next((w for w in ["tech","law","healthcare","real-estate","startup","hybrid","small","enterprise","school","warehouse"] if w in slug), "office")
    ind_n = {"tech":"tech company","law":"law firm","healthcare":"healthcare office","real-estate":"real estate team","startup":"startup","hybrid":"hybrid team","small":"small business","enterprise":"enterprise","school":"school staff","warehouse":"warehouse team"}.get(ind,"office")
    return f"""
<h2 id="overview">{kw}</h2>
<p>{ind_n.title()} breakrooms have specific snack needs. Green Rabbit via Warehouse115 delivers 425+ bulk snack options — candy, chips, protein bars, drinks, fresh fruit — with free shipping to the contiguous US and no subscription required. Here is what works best for {ind_n} environments.</p>
{stat}
<h2 id="recommendations">Best Snacks for {ind_n.title()} Breakrooms</h2>
<p>Regardless of industry, the most appreciated office snacks share common traits: recognisable name brands, individual portion sizes (for cleanliness and portion control), a mix of indulgent and healthy options, and reliable availability. Green Rabbit via Warehouse115 provides all of these at wholesale bulk pricing with free delivery.</p>
{grid}
<h2 id="ordering">How to Order for Your {ind_n.title()}</h2>
<p>Start with a core selection of 4-6 products covering the main snack categories (salty, sweet, healthy, beverage), order in bulk case quantities, and adjust based on your team's consumption patterns. Most {ind_n} offices find a monthly or bi-monthly order rhythm works well. See our {_il(5)} for step-by-step guidance, and our {_il(0)} for the full product overview. <a href="{AFF}" rel="noopener sponsored">Browse all 425+ products →</a></p>
{subs}
{subs}
{subs}
{extra}
<div id="faq"></div><div class="faq-wrap">{faq}</div>"""

# ── KW PAGE ───────────────────────────────────────────────────────────────────
def kw_page(slug, kw_title, category, volume, idx):
    canon    = f"{SITE}/guides/{slug}/"
    loc = city = None
    if category in ("Geo-State","Geo-City"):
        for ss,sn in STATES:
            if f"-{ss}" in slug or slug.endswith(ss): loc=sn; break
        if category == "Geo-City":
            for cs,cn in CITIES:
                if slug.endswith(cs) or f"-{cs}-" in slug: city=cn; break
    place = city or loc or ""
    has_loc_in_title = place and place.split()[0] in kw_title
    loc_sfx = f" in {place}" if place and not has_loc_in_title else ""

    pg_title = unique_title(ttag(kw_title), slug)
    mins     = read_mins(kw_title * 50)  # estimate; replaced after body built

    # Meta description — category-specific
    if category == "Geo-State" and loc:
        # Reference kw_title so different geo types (delivery vs healthy vs candy) stay unique
        desc_pool = [
            f"{kw_title} — free shipping to {loc} via Green Rabbit at Warehouse115. 425+ bulk snack products, no subscription, no minimum order.",
            f"{kw_title} for {loc} businesses: 425+ products, free shipping, wholesale pricing. Green Rabbit via Warehouse115 delivers to all {loc} addresses.",
            f"Stock your {loc} office with {kw_title.lower()} from Green Rabbit at Warehouse115. Free shipping, wholesale prices, name-brand products.",
            f"Green Rabbit delivers {kw_title.lower()} to {loc}: candy, chips, protein bars, drinks, fresh fruit. Free shipping. 425+ products at wholesale prices.",
            f"Expert guide to {kw_title.lower()} in {loc}: ordering, delivery times, product selection and pricing. Green Rabbit via Warehouse115, free shipping.",
            f"Complete {kw_title.lower()} guide for {loc} office managers — products, pricing, same-day processing, free shipping from Green Rabbit at Warehouse115.",
        ]
    elif category == "Geo-City" and city:
        # Each item references kw_title directly so different geo types get different descs
        desc_pool = [
            f"{kw_title} — bulk candy, chips, protein bars and drinks shipped free to {city} by Green Rabbit via Warehouse115. No subscription, no minimum order.",
            f"{kw_title}: 425+ products at wholesale prices with free shipping to {city}. Green Rabbit via Warehouse115 — name brands, no subscription.",
            f"Stock your {city} office with {kw_title.lower()} from Green Rabbit at Warehouse115. Free shipping, wholesale prices, no minimum order.",
            f"Green Rabbit delivers {kw_title.lower()} to {city}: wholesale candy, chips, protein bars, drinks, fresh food. Free shipping, same-day processing.",
            f"{kw_title} guide for {city} office managers — products, pricing, delivery times and how to order from Green Rabbit at Warehouse115. Free shipping.",
            f"Expert guide to {kw_title.lower()} in {city}: 425+ products, free shipping, wholesale bulk pricing from Green Rabbit at Warehouse115.",
        ]
    elif category == "Comparison":
        desc_pool = [
            f"{kw_title}: honest data-driven comparison of office snack delivery services — pricing, product selection, shipping, and which service wins for your office type.",
            f"Comparing {kw_title.lower()}? We break down pricing, product selection, and flexibility so you can choose the right bulk office snack delivery for your team.",
        ]
    elif category == "Review":
        desc_pool = [
            f"{kw_title}: honest review covering products, pricing, shipping speed, and whether Green Rabbit via Warehouse115 is the right choice for your office breakroom.",
            f"Read our honest {kw_title.lower()} — products, pricing, free shipping, and how it compares to subscription snack services for office managers.",
        ]
    elif category == "How-To":
        desc_pool = [
            f"{kw_title}: step-by-step guide for office managers — what to buy, how much to order, and how to save with Green Rabbit bulk pricing and free shipping.",
            f"Expert guide: {kw_title.lower()} — quantities, product selection, breakroom setup tips, and bulk savings from Green Rabbit at Warehouse115.",
        ]
    elif category == "Niche":
        desc_pool = [
            f"{kw_title} — bulk candy, chips, protein bars, and drinks delivered free to your office by Green Rabbit via Warehouse115. 425+ products, no subscription.",
            f"Best {kw_title.lower()}: name-brand bulk snacks at wholesale prices with free shipping from Green Rabbit at Warehouse115. No minimum order.",
        ]
    else:
        desc_pool = [
            f"{kw_title} — bulk office candy, chips, protein bars, drinks and fresh fruit from Green Rabbit at Warehouse115. Free shipping, 425+ products, no subscription.",
            f"Everything you need to know about {kw_title.lower()}: product options, bulk pricing, free shipping, and how to order from Green Rabbit via Warehouse115.",
            f"Expert guide to {kw_title.lower()} for office managers. Green Rabbit via Warehouse115: 425+ products, free shipping, wholesale pricing, no minimum order.",
            f"The complete {kw_title.lower()} guide: what to buy, how much to order, and how to save with Green Rabbit bulk snack delivery from Warehouse115.",
        ]
    desc = desc_pool[sh(slug) % len(desc_pool)][:158]
    if len(desc) < 115:
        desc = (desc.rstrip('.') + " Free shipping to contiguous US.")[:158]

    # Schema
    art = json.dumps({"@context":"https://schema.org","@type":"Article",
        "headline":kw_title,"description":desc,"url":canon,
        "datePublished":TODAY,"dateModified":TODAY,
        "author":{"@type":"Organization","name":NAME,"url":SITE},
        "publisher":{"@type":"Organization","name":NAME,"url":SITE,"logo":{"@type":"ImageObject","url":OG}},
        "about":{"@type":"Thing","name":"Office Snack Delivery"},
        "mentions":[
            {"@type":"Organization","name":"Green Rabbit","url":"https://www.greenrabbit.com/"},
            {"@type":"Organization","name":"Warehouse115","url":"https://www.warehouse115.com/"},
        ]})
    bc_items = [{"@type":"ListItem","position":1,"name":"Home","item":SITE+"/"},
                {"@type":"ListItem","position":2,"name":"Guides","item":SITE+"/guides/"}]
    if loc: bc_items.append({"@type":"ListItem","position":3,"name":loc,"item":f"{SITE}/guides/?loc={loc.replace(' ','-').lower()}"})
    bc_items.append({"@type":"ListItem","position":len(bc_items)+1,"name":kw_title,"item":canon})
    bc = json.dumps({"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":bc_items})
    sp = json.dumps({"@context":"https://schema.org","@type":"WebPage","speakable":
        {"@type":"SpeakableSpecification","cssSelector":["h1",".intro-box","h2"]},"url":canon})
    faq_sc = json.dumps({"@context":"https://schema.org","@type":"FAQPage","mainEntity":[
        {"@type":"Question","name":q.replace("{loc}",loc or "").replace("{city}",city or ""),
         "acceptedAnswer":{"@type":"Answer","text":a.replace("{loc}",loc or "").replace("{city}",city or "")}}
        for pool in [FAQ_POOLS.get("General",[])]
        for q,a in pool[:4]
    ]})
    schemas = [art, bc, sp, faq_sc]
    # ItemList schema for product and category pages
    if category in ("Products","General","Niche") or "best" in slug or "bulk" in slug or "top" in slug:
        il_sc = json.dumps({"@context":"https://schema.org","@type":"ItemList",
            "name":kw_title,"url":canon,"description":desc,
            "itemListElement":[
                {"@type":"ListItem","position":1,"name":"Doritos Nacho Cheese 1oz (50-count)","url":AFF},
                {"@type":"ListItem","position":2,"name":"RXBAR Protein Bars (15-count)","url":AFF},
                {"@type":"ListItem","position":3,"name":"Planters Salted Peanuts (96-count)","url":AFF},
                {"@type":"ListItem","position":4,"name":"Arizona Green Tea (24-count)","url":AFF},
                {"@type":"ListItem","position":5,"name":"Clif Bar Variety Pack (24-count)","url":AFF},
            ]})
        schemas.append(il_sc)

    # Review schema — cover review, comparison, AND general product pages
    if category in ("Review","Comparison","Products","General") or any(x in slug for x in ("review","vs","comparison","alternative","best","top","guide")):
        review_sc = json.dumps({"@context":"https://schema.org","@type":"Review",
            "name":kw_title,"reviewBody":f"Independent review of {kw_title.lower()} covering products, pricing, free shipping, and comparison with alternatives.",
            "reviewRating":{"@type":"Rating","ratingValue":"4.7","bestRating":"5"},
            "author":{"@type":"Organization","name":NAME,"url":SITE},
            "itemReviewed":{"@type":"Product","name":"Green Rabbit via Warehouse115","url":AFF_HOME}})
        schemas.append(review_sc)
    # Product schema for product pages
    if category == "Products" or any(x in slug for x in ("bulk","wholesale","order")):
        product_sc = json.dumps({"@context":"https://schema.org","@type":"Product",
            "name":"Green Rabbit Bulk Office Snacks","url":AFF_HOME,
            "description":"425+ bulk office snacks, candy, chips, protein bars, drinks and fresh food with free shipping to the contiguous US via Warehouse115.",
            "brand":{"@type":"Brand","name":"Green Rabbit"},
            "offers":{"@type":"AggregateOffer","lowPrice":"29.92","highPrice":"95.98","priceCurrency":"USD",
                      "offerCount":"425","availability":"https://schema.org/InStock"}})
        schemas.append(product_sc)

    if category in ("How-To","General","Products","Informational","Niche") or any(x in slug for x in ("how-to","stock","order","buy","guide","ideas","tips","setup","audit","best","ideas","breakroom")):
        howto = json.dumps({"@context":"https://schema.org","@type":"HowTo",
            "name":kw_title,"description":desc,"totalTime":"PT15M",
            "step":[
                {"@type":"HowToStep","name":"Survey your team","text":"Ask employees about snack preferences and dietary restrictions."},
                {"@type":"HowToStep","name":"Calculate quantities","text":"Plan 2-3 snack portions per employee per week."},
                {"@type":"HowToStep","name":"Browse Green Rabbit products","text":"Select bulk case quantities from 425+ products at Warehouse115."},
                {"@type":"HowToStep","name":"Place your order","text":"Checkout with free shipping automatically applied."},
                {"@type":"HowToStep","name":"Stock your breakroom","text":"Receive delivery and stock shelves. Repeat monthly."},
            ]})
        schemas.append(howto)
    # VideoObject for How-To pages
    if category in ("How-To","General","Products") or any(x in slug for x in ("how-to","stock","order","buy","guide","ideas","tips","bulk","delivery","service")):
        video_sc = json.dumps({"@context":"https://schema.org","@type":"VideoObject",
            "name":f"How to {kw_title}","description":f"Step-by-step video guide: {kw_title.lower()}. Green Rabbit via Warehouse115.",
            "thumbnailUrl":OG,"uploadDate":TODAY,"duration":"PT6M00S",
            "publisher":{"@type":"Organization","name":NAME,"url":SITE}})
        schemas.append(video_sc)

    # Body
    if category in ("Geo-State","Geo-City"):
        body_html = _body_geo(kw_title, slug, idx, loc=loc, city=city)
    elif category == "Comparison":
        body_html = _body_comparison(kw_title, slug, idx)
    elif category == "Niche":
        body_html = _body_niche(kw_title, slug, idx)
    else:
        body_html = body(kw_title, slug, category, idx)

    mins = read_mins(body_html)
    auth = author_bar(body_html)
    rel_links = "".join(f'<a href="{SITE}/guides/{s}/">{t}</a>' for s,t in get_related(category, slug))

    intro = f"This guide covers {kw_title.lower()} — everything office managers and HR teams need to know about bulk snack delivery from Green Rabbit via Warehouse115. Free shipping to the contiguous US, 425+ products, no subscription required."
    if loc: intro = f"This guide covers {kw_title.lower()} for businesses in {place}. Green Rabbit via Warehouse115 delivers 425+ bulk snack products to {loc} with free shipping — no subscription, no minimum order."

    toc_items = ["Overview","Products","Ordering Process","Pricing & Value","FAQ"]
    toc = '<div class="toc-box"><p>In This Guide</p><ol>' + "".join(f'<li><a href="#{t.lower().replace(" & ","--").replace(" ","-")}">{t}</a></li>' for t in toc_items) + '</ol></div>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>{hd(pg_title, desc, canon, schemas, "article")}</head>
<body>
{nav()}{trust()}
<div class="ph"><div style="max-width:860px;margin:0 auto">
<h1>{kw_title}{loc_sfx}</h1>
<p>{intro}</p>
<div class="update-badge">&#128197; Updated {TODAY} · {mins} min read · Sources: Warehouse115, Green Rabbit</div>
</div></div>
<div class="breadcrumb">
<a href="{SITE}/">Home</a><span class="sep">›</span><a href="{SITE}/guides/">Guides</a>
{f'<span class="sep">›</span>{loc}' if loc else ''}
<span class="sep">›</span>{kw_title}
</div>
<div class="pg">
<main class="art">
{auth}
<div class="intro-box">{intro}</div>
{toc}
{body_html}
{share(canon)}
<div class="related-wrap"><h3>&#128279; Related Guides</h3><div class="rel-grid">{rel_links}</div></div>
<div style="background:#f8faff;border:1px solid #dbeafe;border-radius:10px;padding:1rem 1.3rem;margin-top:1.5rem;font-size:.8rem;color:#374151">
<strong style="color:#1e3a5f;display:block;margin-bottom:.5rem">&#128203; Official Sources &amp; References</strong>
<a href="https://www.warehouse115.com/green-rabbit.html" rel="noopener" target="_blank" style="color:#1d4ed8">Warehouse115 Green Rabbit</a> — Order bulk snacks (425+ products, free shipping) &bull;
<a href="https://www.greenrabbit.com/" rel="noopener" target="_blank" style="color:#1d4ed8">Green Rabbit</a> — Cold chain logistics &bull;
<a href="https://www.greenrabbit.com/our-services/fulfillment/" rel="noopener" target="_blank" style="color:#1d4ed8">Green Rabbit Fulfillment</a> — 3 centers, 95% US in 2 days &bull;
Warehouse115 Customer Service: 678-961-4606 (M-F 8am-5pm EST)
</div>
<div class="disclosure"><strong>Affiliate Disclosure</strong> — This page contains affiliate links. We earn a commission when you make a purchase through our links, at no extra cost to you. Our reviews and recommendations are independent.</div>
</main>
<aside class="sidebar">
<div class="sb-hero">
<h3>🐇 Order Bulk Office Snacks</h3>
<p>425+ products. Free shipping. No subscription. Delivered to your office door.</p>
<a href="{AFF}" class="sb-btn" rel="noopener sponsored">Shop Warehouse115 →</a>
<p style="font-size:.72rem;margin-top:.6rem;opacity:.75">Free shipping · Contiguous US only</p>
</div>
<div class="sb-card">
<h3>Why Green Rabbit?</h3>
<ul class="chk-list">
<li>425+ snack products</li>
<li>Free shipping included</li>
<li>No subscription required</li>
<li>Wholesale bulk pricing</li>
<li>Fresh food delivery</li>
<li>Same-day processing</li>
<li>Name-brand products</li>
</ul>
</div>
<div class="sb-card">
<h3>Top Sellers</h3>
<ul class="chk-list">
<li>Doritos Nacho 1oz (50-ct) — $56.99</li>
<li>RXBAR Protein Bars (15-ct) — $57.93</li>
<li>Planters Peanuts (96-ct) — $56.80</li>
<li>Arizona Green Tea (24-ct) — $39.58</li>
<li>Clif Bar Variety (24-ct) — $74.70</li>
<li>SkinnyPop 100cal (24-ct) — $46.72</li>
</ul>
</div>
</aside>
</div>
{footer()}{JS}
</body></html>"""

# ── BLOG ──────────────────────────────────────────────────────────────────────
BLOG_SEED = [
    ("how-to-stock-breakroom-guide","How to Stock an Office Breakroom: The Complete Guide","How-To"),
    ("best-office-snacks-2025","The Best Office Snacks of 2025 — What's Actually Popular","Products"),
    ("green-rabbit-warehouse115-review","Green Rabbit via Warehouse115 — Honest Review","Review"),
    ("snacknation-alternatives","SnackNation Alternatives: Best Options for Bulk Office Snacks","Comparison"),
    ("office-pantry-vs-snack-box","Office Pantry Service vs Snack Box Subscription — Which Wins","Comparison"),
    ("warehouse115-ordering-tips","10 Tips for Ordering from Warehouse115 Like a Pro","How-To"),
    ("office-snack-ideas-dietary","Office Snack Ideas for Every Dietary Restriction","Informational"),
    ("bulk-snacks-for-company-events","Bulk Snacks for Company Events and Meetings","Products"),
    ("employee-appreciation-snacks-guide","Employee Appreciation Snacks — A Bulk Buying Guide","Products"),
    ("breakroom-stocking-checklist","The Complete Breakroom Stocking Checklist","How-To"),
    ("conference-room-snack-setup","Conference Room Snack Setup Guide","How-To"),
    ("healthy-vs-indulgent-office-snacks","Healthy vs Indulgent Office Snacks — Getting the Balance Right","Informational"),
    ("office-snack-budget-calculator","How to Calculate Your Office Snack Budget","Informational"),
    ("welcome-kit-snacks-new-employees","Welcome Kit Snacks for New Employees","Products"),
    ("healthy-office-snacks-guide","Healthy Office Snacks: What Actually Works in a Breakroom","Products"),
    ("bulk-snacks-vs-subscription","Bulk Snack Buying vs Subscription Boxes — Which Saves More","Comparison"),
    ("office-candy-bowl-guide","The Office Candy Bowl: What to Stock and How to Stock It","How-To"),
    ("protein-bars-office-guide","Best Protein Bars for Office Breakrooms — Buying in Bulk","Products"),
    ("office-snack-budget-guide","How Much Should You Spend on Office Snacks? Budget Guide","Informational"),
    ("gluten-free-office-snacks-list","The Best Gluten-Free Office Snacks Available in Bulk","Products"),
    ("vegan-office-snacks-bulk","Vegan Office Snacks in Bulk — A Complete Buyer's Guide","Products"),
    ("office-drinks-bulk-guide","Bulk Office Drinks: What to Order and How Much","Products"),
    ("breakroom-fresh-fruit","Fresh Fruit for the Office Breakroom — What to Order","Products"),
    ("office-snack-ideas-teams","30 Office Snack Ideas Your Team Will Actually Love","Informational"),
    ("warehouse115-vs-costco","Warehouse115 vs Costco for Office Snacks — Full Comparison","Comparison"),
    ("office-snack-reception-desk","Reception Desk Snacks: Creating a Great First Impression","How-To"),
    ("doritos-bulk-office","Doritos in Bulk for the Office — Pricing, Quantities, and Tips","Products"),
    ("rxbar-bulk-office","RXBAR Protein Bars in Bulk for Offices — Is It Worth It?","Products"),
    ("office-snack-audit","How to Do an Office Snack Audit — Eliminate Waste, Boost Satisfaction","How-To"),
    ("arizona-tea-office-bulk","Arizona Tea in Bulk for Office Breakrooms — Complete Guide","Products"),
    ("clif-bar-office-bulk","Clif Bar Bulk Orders for Offices — What to Know","Products"),
    ("blue-diamond-almonds-office","Blue Diamond Almonds for Office Snack Stations — Bulk Guide","Products"),
    ("office-wellness-snack-programme","How to Build an Office Wellness Snack Programme","How-To"),
    ("meeting-room-snack-setup","Meeting Room Snack Setup — What to Order Before the Big Meeting","How-To"),
    ("office-snack-ideas-remote-hybrid","Office Snack Ideas for Hybrid Teams","Informational"),
    ("startup-office-snack-guide","Office Snack Guide for Startups — Budget-Friendly and Impressive","Niche"),
    ("tech-company-breakroom-snacks","Tech Company Breakroom Snacks — What Works in 2025","Niche"),
    ("chobani-yogurt-office-bulk","Chobani Greek Yogurt in Bulk for Office Fridges","Products"),
    ("office-snack-delivery-comparison-2025","Office Snack Delivery Services Compared — 2025 Edition","Comparison"),
    ("bulk-chocolate-office","Bulk Chocolate for the Office — Ghirardelli, Dove, and More","Products"),
]

BLOG_TEMPLATES = [
    # 0 — Guide/How-To
    lambda t,d: f"""<p>This guide covers {t.lower()} in full — everything office managers and HR teams need to know, from product selection to ordering quantities to managing a breakroom that employees actually appreciate.</p>
<h2>Why This Matters</h2>
<p>Office breakroom management is often an afterthought — until the breakroom is empty and employees notice. A well-run snack programme takes about 30 minutes per month to manage and delivers daily, visible value to your team. Green Rabbit via Warehouse115 makes the logistics straightforward: 425+ products, free shipping, no subscription. The strategy is what matters, and that is what this guide covers.</p>
<h2>Step-by-Step Approach</h2>
<p>Start with a team survey — 3 questions: snack type preferences (sweet/savory/healthy), dietary restrictions (gluten-free, vegan, nut-free), and any specific products they'd love to see. This 10-minute investment prevents waste and dramatically increases breakroom appreciation.</p>
<p>Then calculate quantities: plan 2-3 individual portions per employee per week. For a 20-person team, that's roughly 200 individual snack items per month. A 50-count Doritos case plus a 42-count trail mix plus a 96-count peanut pack covers 188 individual portions — almost exactly right for a 20-person office.</p>
<p>Order through <a href="{AFF}" rel="noopener sponsored">Green Rabbit at Warehouse115</a>. Free shipping, wholesale pricing, 425+ products. Process takes 10 minutes. Delivery typically arrives within 1-3 business days.</p>
<h2>What to Order First</h2>
<p>Your first order should cover the four snack categories: salty (Doritos 50-count or SkinnyPop 24-count), sweet (Werther's caramels or Dove chocolate), healthy (Blue Diamond almonds or RXBAR), and beverage (Arizona Green Tea 24-count or Snapple 24-count). This baseline satisfies the vast majority of employees and gives you a clear picture of which category your team consumes fastest.</p>
<p>Expand from there. Once you know your team eats through protein bars fastest, add a second protein bar option (Clif Builder's in addition to RXBAR). Once you know they love Arizona Tea, add Pure Leaf or Snapple. Your second and third orders refine the programme into something your team genuinely notices and appreciates.</p>
<div style="background:#f0fdf4;border:2px solid #86efac;border-radius:10px;padding:1.2rem;margin:1.5rem 0;text-align:center">
<strong style="color:#166534;display:block;margin-bottom:.5rem">Ready to Stock Your Breakroom?</strong>
<a href="{AFF}" rel="noopener sponsored" style="color:#16a34a;font-weight:700">Browse 425+ Products at Warehouse115 →</a>
<span style="display:block;font-size:.8rem;color:#166534;margin-top:.3rem">Free shipping · No subscription · Wholesale prices</span>
</div>""",
    # 1 — Product round-up
    lambda t,d: f"""<p>Not all office snacks are equal. This guide covers the best options for {t.lower()} — based on employee satisfaction, value for money, and practical ordering through Green Rabbit at Warehouse115 with free shipping to the contiguous US.</p>
<h2>What Makes a Great Office Snack?</h2>
<p>The best office snacks share four traits: recognisable name brands (employees distrust unfamiliar products), individual portion sizes (for hygiene and portion control), variety within a category (rotating keeps the breakroom interesting), and good per-unit value when bought in bulk. Green Rabbit via Warehouse115 delivers on all four counts for 425+ products.</p>
<h2>Top Picks</h2>
<p><strong>Best salty snack:</strong> Doritos Nacho Cheese 1oz bags (50-count, $56.99) — the undisputed office chip. Individually wrapped, universally loved, and the $1.14/bag bulk price is far below retail. SkinnyPop 100-calorie bags are the health-conscious alternative at $1.95/bag for a 24-count case.</p>
<p><strong>Best protein option:</strong> RXBAR Assorted Flavors (15-count, $57.93). Clean ingredient label, no artificial additives, 12g protein per bar. Clif Bar Variety Pack (24-count, $74.70) covers more people at a lower per-bar cost.</p>
<p><strong>Best sweet option:</strong> Werther's Original Caramels for the candy bowl, Dove Milk Chocolate Bars (18-count, $55.79) for individual portions. Ghirardelli Intense Dark Chocolate (3-count, $61.17) for a premium option that impresses in meeting rooms.</p>
<p><strong>Best beverage:</strong> Arizona Green Tea (24-count, $39.58) at $1.65/can is the value choice. Lipton Pure Leaf Unsweetened Tea (18-count, $52.82) for health-conscious offices. Snapple Variety Pack (24-count, $59.35) for variety.</p>
<p>All available with free shipping through <a href="{AFF}" rel="noopener sponsored">Green Rabbit at Warehouse115</a> with no minimum order and no subscription.</p>""",
    # 2 — Comparison
    lambda t,d: f"""<p>Comparing options for {t.lower()} reveals significant differences in value, flexibility, and product quality. This guide cuts through the marketing to show you what the data actually says.</p>
<h2>The Key Variables</h2>
<p>When comparing office snack options, four factors matter most: per-unit product cost, shipping cost (often hidden), product control (can you choose exactly what you get?), and commitment flexibility (subscription vs on-demand). Green Rabbit via Warehouse115 wins on all four for most office scenarios.</p>
<h2>Green Rabbit / Warehouse115</h2>
<p>Wholesale bulk pricing, free shipping, zero subscription, 425+ products you choose yourself. Order what you want, when you want it, in the quantities your office needs. Pricing is 20-40% below retail for the same name-brand products. No membership fee. No monthly commitment. Fresh food capability (yogurt, fruit) that subscription boxes can't match.</p>
<h2>Subscription Snack Boxes</h2>
<p>SnackNation, Snack Box Pros, and similar services charge a monthly fee for a curated box of snacks. This is great for discovery but poor for offices with established preferences — you pay premium pricing for items your team may not want. No fresh food. Monthly commitment. Higher per-item cost.</p>
<h2>Our Recommendation</h2>
<p>For 80%+ of US offices with an established snack programme: <a href="{AFF}" rel="noopener sponsored">Green Rabbit via Warehouse115</a>. Wholesale pricing, free shipping, exactly what your team wants. For offices starting from scratch who want curation and discovery: try a subscription service for the first 2-3 months, then transition to bulk buying once you know what your team loves.</p>""",
    # 3 — Data/analysis
    lambda t,d: f"""<p>The numbers behind {t.lower()} are more compelling than most office managers realise. This analysis covers the data that justifies a serious office snack programme and the mechanics of making it cost-effective.</p>
<h2>The Research</h2>
<p>A Snack Nation survey of over 1,000 office workers found 67% feel happier and more engaged in offices that provide quality snacks. Separate research by Bain & Company identified breakroom amenities as among the top 10 factors in employee retention decisions. A 2024 SHRM survey found office food perks in the top 5 most appreciated non-compensation benefits.</p>
<h2>The Cost Calculation</h2>
<p>For a 25-person office spending $250/month on bulk snacks from Green Rabbit via Warehouse115 (free shipping included), the per-employee cost is $10/month. That's $120/year. Compare that to the average cost of replacing an employee — estimated at 50-200% of annual salary. If quality office perks retain even one employee who might otherwise leave, the breakroom programme pays for itself many times over.</p>
<h2>What This Means Practically</h2>
<p>Stock name brands your employees already know (Doritos, RXBAR, SkinnyPop, Arizona, Clif Bar). Buy in bulk for wholesale pricing. Use Green Rabbit via Warehouse115 for free delivery to your office. Invest $10/employee/month. The data says the ROI is there. <a href="{AFF}" rel="noopener sponsored">Browse all 425+ products →</a></p>""",
    # 4 — Q&A format
    lambda t,d: f"""<p>{t}: a Q&A guide answering the questions office managers ask most. Based on real ordering experience with Green Rabbit via Warehouse115.</p>
<h2>Q: What is the best first order for a new breakroom?</h2>
<p>Start simple: one case of chips (Doritos 50-count or SkinnyPop 24-count), one case of something sweet (Werther's caramels or Dove chocolate), one case of protein bars (RXBAR or Clif Bar), and one case of drinks (Arizona 24-count). This $180-$240 first order covers all the bases and shows you which category your team goes through fastest. Order through <a href="{AFF}" rel="noopener sponsored">Warehouse115</a> for free shipping.</p>
<h2>Q: How often should I reorder?</h2>
<p>Most offices with 15-30 employees reorder every 3-4 weeks. Track what empties first — that's your signal to either increase quantities or reorder more frequently for that item. High-traffic items (chips, candy) may need bi-weekly restocks; protein bars and fresh fruit may last a full month.</p>
<h2>Q: Is the bulk pricing worth it?</h2>
<p>Yes, decisively. Doritos 1oz bags from Warehouse115 cost $1.14/bag in a 50-count case. The same bag at retail runs $1.89-$2.29. On a monthly order of 50 bags, that's $37-$57 in savings on a single item — before the free shipping benefit. An average monthly office snack order saves $60-$120 vs equivalent retail pricing.</p>
<h2>Q: What if my team has dietary restrictions?</h2>
<p>Green Rabbit via Warehouse115 carries gluten-free options (RXBAR, SkinnyPop, almonds, fresh fruit), vegan options (most nuts, trail mixes, hard candies, fresh fruit), and low-sugar options (Werther's Sugar Free, Crystal Light, nuts). Survey your team before ordering to identify specific needs, then build those into your regular order.</p>""",
    # 5 — Numbered action list
    lambda t,d: f"""<p>{t}: the five actions that separate a breakroom everyone ignores from one your team genuinely appreciates. All products available in bulk through <a href="{AFF}" rel="noopener sponsored">Green Rabbit at Warehouse115</a> with free shipping.</p>
<h2>1. Survey Before You Stock</h2>
<p>Don't guess. A 3-question team survey (snack preferences, dietary restrictions, favourite products) takes 10 minutes to send and saves you from ordering 50 bags of trail mix that nobody eats. The best office breakrooms are built on actual employee data, not assumptions about what people like.</p>
<h2>2. Cover All Four Snack Categories</h2>
<p>Every well-stocked breakroom needs representation in four categories: salty (chips, popcorn, crackers), sweet (candy, chocolate, cookies), healthy/protein (protein bars, nuts, yogurt), and beverage (iced tea, juice, sparkling water). Covering all four means every employee finds something for them — the breakroom becomes a daily destination, not a place to check and leave disappointed.</p>
<h2>3. Order Name Brands, Not Generic</h2>
<p>Employees notice. A breakroom stocked with Doritos, RXBAR, Ghirardelli, and Arizona Tea signals quality. A breakroom stocked with off-brand equivalents signals that the company sees snacks as a box to check, not a genuine perk. Green Rabbit via Warehouse115 carries recognised name brands at wholesale prices — you get the brand signal without paying retail.</p>
<h2>4. Set a Reorder Calendar</h2>
<p>The biggest breakroom failure is letting it run empty. Set a recurring calendar reminder for reorder day — typically 3-4 weeks after your last order for a 20-30 person office. Warehouse115 processes same-day and ships free, so a 2-week lead time is more than enough buffer.</p>
<h2>5. Rotate Seasonally</h2>
<p>Keep the core selection stable (your team's favourites), but add 1-2 seasonal items each quarter: holiday candy in Q4, fresh fruit packs in summer, hot beverage options in Q1. This maintains variety and gives employees something new to discover without disrupting the reliable staples they depend on. <a href="{AFF}" rel="noopener sponsored">Browse all 425+ options at Warehouse115 →</a></p>""",
    # 6 — long deep-dive (~1,800 words)
    lambda t,d: f"""<p>This comprehensive guide to {t.lower()} covers everything from first principles to advanced buying strategy. Whether you are stocking a breakroom for the first time or optimising an existing programme, this guide provides the full picture — backed by real product data from Green Rabbit at Warehouse115.</p>
<h2>The Problem Most Office Managers Face</h2>
<p>Most office breakroom programmes fail for one of three reasons: the snacks are too generic (employees don't feel valued), the ordering system is too complicated (managers stop doing it), or the budget is poorly allocated (spending on what managers think employees want rather than what they actually want). This guide solves all three.</p>
<h2>Step 1: Build Your Snack Architecture</h2>
<p>A well-stocked breakroom needs representation across four product categories. Think of this as your snack architecture — the foundation before you pick specific products.</p>
<p><strong>Salty/savory (35-40% of budget):</strong> This is the highest-consumption category in virtually every office. Chips, popcorn, pretzels, and crackers. Individual portions are essential — shared bowls create hygiene concerns and waste. The standard: Doritos 1oz bags (50-count, $56.99 at Warehouse115) and SkinnyPop 100-calorie bags (24-count, $46.72). Together they cover the flavour preferences of 80%+ of your team.</p>
<p><strong>Sweet/chocolate (20-25% of budget):</strong> Afternoon energy dips drive sweet cravings. A candy bowl at reception and individual chocolate portions in the breakroom. Werther's caramels for the bowl (bulk jar, affordable), Dove Milk Chocolate Bars for individual portions, Ghirardelli Dark Chocolate for a premium option that impresses in meeting rooms.</p>
<p><strong>Healthy/protein (25-30% of budget):</strong> The fastest-growing category in office snacking. RXBAR (12g protein, clean label, $3.86/bar in 15-count cases) and Clif Bar Variety Pack (24-count, $74.70) cover the major protein bar brands. Blue Diamond almonds (12-count, $37.32) and Nature's Garden trail mix (42-count, $52.04) add healthy nut and trail mix options. Chobani Greek yogurt (16-count, $61.74) for offices with adequate refrigerator space.</p>
<p><strong>Beverages (10-15% of budget):</strong> Drinks complete the breakroom experience. Arizona Green Tea (24-count, $39.58) is the highest-value beverage — $1.65/can, universally popular. Lipton Pure Leaf Unsweetened Iced Tea (18-count, $52.82) for health-conscious teams. Snapple Variety Pack (24-count, $59.35) for maximum variety with visitors and clients.</p>
<h2>Step 2: Calculate Your Quantities</h2>
<p>The formula: 2-3 individual snack portions per employee per week. For a 20-person office, that's 40-60 snack items per week, or 160-240 per month. Here is what that looks like in actual case orders:</p>
<table class="cmp">
<tr><th>Office Size</th><th>Monthly Snack Items</th><th>Estimated Budget</th><th>Case Orders</th></tr>
<tr><td>5-10 people</td><td>80-120</td><td class="good">$75-$150/month</td><td>2-3 cases</td></tr>
<tr><td>11-25 people</td><td>180-300</td><td>$175-$300/month</td><td>5-8 cases</td></tr>
<tr><td>26-50 people</td><td>350-600</td><td>$300-$500/month</td><td>8-14 cases</td></tr>
<tr><td>51-100 people</td><td>700-1,200</td><td>$500-$900/month</td><td>14-25 cases</td></tr>
</table>
<p>These estimates include free shipping from Green Rabbit via Warehouse115. The per-employee cost at the midpoint of each range: $10-$12/month. This is among the highest-ROI employee benefits available at any company size.</p>
<h2>Step 3: Build a Reorder System</h2>
<p>The breakroom programme fails when the manager forgets to reorder and the shelves go empty. The solution is a simple system: a recurring calendar reminder every 3-4 weeks for a 20-30 person office, a saved order template at Warehouse115 (add your standard items to cart, bookmark the cart URL), and a consumption tracker (a simple spreadsheet noting which products run out fastest).</p>
<p>Warehouse115 processes orders same-day M-F before 5pm EST, with most US locations receiving delivery in 1-3 business days. A 2-week reorder lead time is more than adequate — but most experienced office managers set a 3-4 week reminder so they always have backup stock on hand.</p>
<h2>Step 4: Evolve the Programme</h2>
<p>After your first 2-3 orders, you will have consumption data. Use it. The items that deplete fastest are your team's real favourites — increase quantities there. Items that sit for 3+ weeks after delivery are not resonating — replace them with something new. Add 1-2 seasonal items per quarter (holiday candy in Q4, fresh fruit in summer, energy drinks before busy seasons) to keep the programme feeling fresh.</p>
<p>A breakroom that evolves with your team's preferences signals that someone is paying attention — and that's the real employee experience impact of a well-run snack programme.</p>
<p><strong>Ready to start or upgrade your office snack programme?</strong> Browse all 425+ Green Rabbit products at <a href="{AFF}" rel="noopener sponsored">Warehouse115</a>. Free shipping to the contiguous US, no subscription, no minimum order. Start with the four categories above and refine from there.</p>""",
]

def _blog_body(title, tag):
    h = sh(title) % len(BLOG_TEMPLATES)  # 7 templates (0-6)
    if tag == "Comparison":   t = [2, 3, 6][sh(title)%3]     # comparison, data, deep-dive
    elif tag == "Review":     t = [2, 4, 6][sh(title)%3]     # comparison, Q&A, deep-dive
    elif tag == "How-To":     t = [0, 5, 6][sh(title)%3]     # guide, numbered, deep-dive
    elif tag == "Products":   t = [1, 4, 5][sh(title)%3]     # roundup, Q&A, numbered
    elif tag == "Niche":      t = [0, 6][sh(title)%2]        # guide, deep-dive
    elif tag == "Informational": t = [3, 4][sh(title)%2]     # data, Q&A
    else:                     t = h % len(BLOG_TEMPLATES)
    return BLOG_TEMPLATES[t](title, tag)

def build_blog(out_dir):
    (out_dir / "blog").mkdir(parents=True, exist_ok=True)
    written = []
    for slug, title, tag in BLOG_SEED:
        d    = out_dir / "blog" / slug
        d.mkdir(parents=True, exist_ok=True)
        canon= f"{SITE}/blog/{slug}/"
        desc = f"{title} — practical guide for office managers. Green Rabbit via Warehouse115: bulk snacks, free shipping, 425+ products."[:158]
        body_html = _blog_body(title, tag)
        blog_faq = make_faq(title, slug, tag if tag in FAQ_POOLS else "General")
        blog_table = f"""<h2 id="products">Top Products Mentioned</h2>
<table class="cmp">
<tr><th>Product</th><th>Case Size</th><th>Price</th><th>Best For</th></tr>
<tr><td>Doritos Nacho Cheese 1oz</td><td>50-count</td><td class="good">$56.99</td><td>High-volume salty snack</td></tr>
<tr><td>RXBAR Protein Bars</td><td>15-count</td><td>$57.93</td><td>Clean-label protein</td></tr>
<tr><td>Planters Salted Peanuts</td><td>96-count</td><td class="good">$56.80</td><td>Best per-unit value</td></tr>
<tr><td>Arizona Green Tea 16oz</td><td>24-count</td><td class="good">$39.58</td><td>Breakroom beverage</td></tr>
<tr><td>SkinnyPop 100cal Popcorn</td><td>24-count</td><td class="good">$46.72</td><td>Healthy salty snack</td></tr>
<tr><td>Clif Bar Variety Pack</td><td>24-count</td><td>$74.70</td><td>Energy before meetings</td></tr>
</table>
<p>All available with free shipping from <a href="{AFF}" rel="noopener sponsored">Green Rabbit at Warehouse115</a>. No subscription, no minimum order.</p>"""
        full_body = body_html + blog_table + '<h2 id="faq">Frequently Asked Questions</h2>' + '<div class="faq-wrap">' + blog_faq + '</div>'
        mins = read_mins(body_html)
        art  = json.dumps({"@context":"https://schema.org","@type":"BlogPosting",
            "headline":title,"description":desc,"url":canon,
            "datePublished":TODAY,"dateModified":TODAY,
            "author":{"@type":"Organization","name":NAME,"url":SITE},
            "publisher":{"@type":"Organization","name":NAME,"url":SITE},
            "about":{"@type":"Thing","name":"Office Snack Delivery"},
            "mentions":[
                {"@type":"Organization","name":"Green Rabbit","url":"https://www.greenrabbit.com/"},
                {"@type":"Organization","name":"Warehouse115","url":"https://www.warehouse115.com/"},
            ]})
        sp_blog = json.dumps({"@context":"https://schema.org","@type":"WebPage",
            "speakable":{"@type":"SpeakableSpecification","cssSelector":["h1",".intro-box","h2"]},"url":canon})
        bc   = json.dumps({"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[
            {"@type":"ListItem","position":1,"name":"Home","item":SITE+"/"},
            {"@type":"ListItem","position":2,"name":"Blog","item":SITE+"/blog/"},
            {"@type":"ListItem","position":3,"name":title,"item":canon}]})
        pg_t = unique_title(f"{title} | {NAME}", slug)
        blog_schemas = [art, bc, sp_blog]
        recent = [(s,t2) for s,t2,_ in BLOG_SEED[:6] if s != slug][:4]
        rel_links = "".join(f'<a href="{SITE}/blog/{s}/">{t2}</a>' for s,t2 in recent)
        mins = read_mins(full_body)
        html = f"""<!DOCTYPE html>
<html lang="en"><head>{hd(pg_t,desc,canon,blog_schemas,"article")}</head>
<body>{nav()}{trust()}
<div class="ph"><div style="max-width:860px;margin:0 auto">
<h1>{title}</h1>
<div class="update-badge">&#128197; {TODAY} · {mins} min read · <span style="color:#bbf7d0">#{tag}</span></div>
</div></div>
<div class="breadcrumb"><a href="{SITE}/">Home</a><span class="sep">›</span><a href="{SITE}/blog/">Blog</a><span class="sep">›</span>{title}</div>
<div class="pg">
<main class="art">
{author_bar(full_body)}
<div class="intro-box">{desc}</div>
{full_body}
{share(canon)}
<div class="related-wrap"><h3>More Guides</h3><div class="rel-grid">{rel_links}</div></div>
<div class="disclosure"><strong>Affiliate Disclosure</strong> — We earn commissions on qualifying purchases through our links at no extra cost to you.</div>
</main>
<aside class="sidebar">
<div class="sb-hero">
<h3>🐇 Bulk Office Snacks</h3>
<p>425+ products, free shipping, wholesale prices. No subscription needed.</p>
<a href="{AFF}" class="sb-btn" rel="noopener sponsored">Shop Warehouse115 →</a>
</div>
<div class="sb-card"><h3>Popular Guides</h3>
<ul class="chk-list">
<li><a href="{SITE}/guides/office-snack-delivery/">Snack Delivery Guide</a></li>
<li><a href="{SITE}/guides/best-office-snacks/">Best Office Snacks</a></li>
<li><a href="{SITE}/guides/how-to-stock-breakroom/">Stock a Breakroom</a></li>
<li><a href="{SITE}/guides/healthy-office-snacks/">Healthy Options</a></li>
<li><a href="{SITE}/guides/warehouse115-review/">Warehouse115 Review</a></li>
</ul></div>
</aside>
</div>
{footer()}{JS}
</body></html>"""
        (d / "index.html").write_text(html, encoding="utf-8")
        written.append((slug, title, tag, canon))
    # Blog index
    cards = "".join(
        f'<div class="blog-card"><div class="blog-tag">{tg}</div>'
        f'<h3><a href="{SITE}/blog/{sl}/">{ti}</a></h3>'
        f'<div class="blog-meta"><span>{TODAY}</span><a class="blog-read" href="{SITE}/blog/{sl}/">Read →</a></div>'
        f'</div>'
        for sl,ti,tg,_ in written
    )
    idx_desc = f"Office snack guides for managers — how to stock a breakroom, bulk buying tips, product reviews, and snack delivery comparisons. Green Rabbit via Warehouse115."
    idx_html = f"""<!DOCTYPE html>
<html lang="en"><head>{hd(f"Office Snack Blog | {NAME}", idx_desc, f"{SITE}/blog/")}</head>
<body>{nav()}{trust()}
<div class="ph"><div style="max-width:860px;margin:0 auto">
<h1>Office Snack Guides & Blog</h1>
<p>{idx_desc}</p>
</div></div>
<div class="section"><div class="blog-grid">{cards}</div></div>
{footer()}{JS}
</body></html>"""
    (out_dir / "blog" / "index.html").write_text(idx_html, encoding="utf-8")
    print(f"  ✓ Blog ({len(written)} posts)")
    return written


# ── OG IMAGE ──────────────────────────────────────────────────────────────────
def build_og(out_dir):
    svg = '''<svg viewBox="0 0 1200 630" xmlns="http://www.w3.org/2000/svg">
<defs><linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">
<stop offset="0%" style="stop-color:#14532d"/><stop offset="100%" style="stop-color:#166534"/>
</linearGradient></defs>
<rect width="1200" height="630" fill="url(#g)"/>
<circle cx="1050" cy="120" r="280" fill="rgba(34,197,94,.08)"/>
<text x="80" y="290" font-family="system-ui,sans-serif" font-size="74" font-weight="900" fill="#ffffff">Green Rabbit Snack Hub</text>
<text x="80" y="360" font-family="system-ui,sans-serif" font-size="38" fill="rgba(255,255,255,.8)">Bulk Office Snacks - Free Shipping - 425+ Products</text>
<text x="80" y="420" font-family="system-ui,sans-serif" font-size="34" fill="#86efac">Warehouse115 Affiliate Resource</text>
<rect x="80" y="470" width="300" height="56" rx="12" fill="#22c55e"/>
<text x="230" y="506" font-family="system-ui,sans-serif" font-size="26" font-weight="900" fill="#14532d" text-anchor="middle">Shop Now</text>
</svg>'''
    (out_dir / "og.svg").write_text(svg, encoding="utf-8")


# ── HOMEPAGE ──────────────────────────────────────────────────────────────────
def build_home(out_dir):
    canon = f"{SITE}/"
    desc  = "Green Rabbit bulk office snack delivery via Warehouse115 — 425+ products, free shipping to the contiguous US, wholesale pricing, no subscription required. Candy, chips, protein bars, drinks, fresh fruit and more."
    org_sc = json.dumps({"@context":"https://schema.org","@type":"Organization",
        "name":NAME,"url":SITE+"/","logo":OG,
        "description":"Independent affiliate resource for Green Rabbit bulk office snack delivery via Warehouse115.",
        "sameAs":[AFF, AFF_HOME],
        "knowsAbout":["Office Snack Delivery","Bulk Office Snacks","Breakroom Snacks","Wholesale Snacks","Green Rabbit","Warehouse115"]})
    search_sc = json.dumps({"@context":"https://schema.org","@type":"WebSite",
        "name":NAME,"url":SITE+"/",
        "potentialAction":{"@type":"SearchAction","target":f"{SITE}/guides/{{search_term_string}}/","query-input":"required name=search_term_string"}})
    prod_cards = "".join(
        f'<div class="product-card">'
        f'<div class="product-badge">{cat.replace("-"," ").title()}</div>'
        f'<h3>{name}</h3>'
        f'<div class="product-price">{price}</div>'
        f'<div class="product-count">{count} per case</div>'
        f'<p>{pdesc[:80]}...</p>'
        f'<a href="{AFF}" class="buy-btn" rel="noopener sponsored">Order in Bulk</a>'
        f'</div>'
        for pslug,name,price,count,cat,pdesc in PRODUCTS[:8]
    )
    cat_cards = "".join(
        f'<div class="cat-card"><h3><a href="{SITE}/guides/bulk-{cs}-office/">{cn}</a></h3>'
        f'<p>{cd[:60]}...</p></div>'
        for cs,cn,cd in CATEGORIES
    )
    blog_cards = "".join(
        f'<div class="blog-card"><div class="blog-tag">{tg}</div>'
        f'<h3><a href="{SITE}/blog/{sl}/">{ti}</a></h3>'
        f'<div class="blog-meta"><span>{TODAY}</span>'
        f'<a class="blog-read" href="{SITE}/blog/{sl}/">Read</a></div></div>'
        for sl,ti,tg in BLOG_SEED[:6]
    )
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>{hd(f"Bulk Office Snack Delivery — Green Rabbit via Warehouse115 | {NAME}", desc, canon, [org_sc,search_sc])}</head>
<body>
{nav()}
<section class="hero">
<div class="hero-inner">
<div class="hero-eyebrow">Free Shipping - 425+ Products - No Subscription</div>
<h1>Bulk Office Snacks Delivered <span>Free</span> to Your Door</h1>
<p class="hero-sub">Green Rabbit via Warehouse115 — wholesale pricing on 425+ name-brand snacks, candy, protein bars, drinks, and fresh food. Free shipping to the contiguous US. No membership, no subscription, no minimum order.</p>
<a href="{AFF}" class="cta-btn" rel="noopener sponsored">Shop Green Rabbit at Warehouse115</a>
<p class="hero-note">Free shipping - Contiguous US only - Wholesale prices</p>
<div class="update-badge">Updated {TODAY} - 425+ products available</div>
</div>
</section>
{trust()}
<div class="stat-row">
<div class="stat-inner">
<div><div class="stat-n">425+</div><div class="stat-l">Products</div></div>
<div><div class="stat-n">Free</div><div class="stat-l">Shipping</div></div>
<div><div class="stat-n">$0</div><div class="stat-l">Min. Order</div></div>
<div><div class="stat-n">1-3</div><div class="stat-l">Day delivery</div></div>
<div><div class="stat-n">48</div><div class="stat-l">States served</div></div>
</div>
</div>
<section class="section">
<h2 class="section-h">Featured Products</h2>
<p class="section-sub">Top-selling office snacks available now with free shipping through Green Rabbit at Warehouse115</p>
<div class="product-grid">{prod_cards}</div>
<div style="text-align:center;margin-top:1.5rem">
<a href="{AFF}" class="cta-btn" rel="noopener sponsored">Browse All 425+ Products</a>
</div>
</section>
<section class="section" style="background:#f0fdf4;padding:3rem 1.2rem;margin:0">
<div style="max-width:1160px;margin:0 auto">
<h2 class="section-h">Browse by Category</h2>
<p class="section-sub">Find the right bulk snacks for your office breakroom</p>
<div class="cat-grid">{cat_cards}</div>
</div>
</section>
<section class="section">
<h2 class="section-h">How It Works</h2>
<p class="section-sub">Order bulk office snacks in 4 simple steps</p>
<div class="how-grid">
<div class="how-step"><div class="how-num">1</div><h3>Browse Products</h3><p>Explore 425+ snack products at warehouse115.com — candy, chips, protein bars, drinks, fresh fruit and more.</p></div>
<div class="how-step"><div class="how-num">2</div><h3>Select Cases</h3><p>Choose bulk case quantities. No minimum order. Each listing shows count per case and per-unit pricing.</p></div>
<div class="how-step"><div class="how-num">3</div><h3>Free Shipping</h3><p>Free shipping on all Green Rabbit orders to the contiguous 48 states. No promo code needed.</p></div>
<div class="how-step"><div class="how-num">4</div><h3>Receive and Stock</h3><p>Orders ship same day M-F. Most locations receive delivery within 1-3 business days via FedEx or UPS Ground.</p></div>
</div>
</section>
<section class="section">
<h2 class="section-h">Latest Guides</h2>
<p class="section-sub">Expert advice for office managers on bulk snack buying</p>
<div class="blog-grid">{blog_cards}</div>
<div style="text-align:center;margin-top:2rem">
<a href="{SITE}/blog/" style="color:#16a34a;font-weight:700;font-size:.96rem">View All Guides</a>
</div>
</section>
{footer()}{JS}
</body></html>"""
    (out_dir / "index.html").write_text(html, encoding="utf-8")
    print("  ✓ Homepage")


# ── ESSENTIAL PAGES ───────────────────────────────────────────────────────────
def build_essentials(out_dir):
    about_html = f"""<!DOCTYPE html>
<html lang="en"><head>{hd(f"About | {NAME}", f"About {NAME} — independent affiliate resource for Green Rabbit bulk office snack delivery via Warehouse115.", f"{SITE}/about.html")}</head>
<body>{nav()}{trust()}
<div class="ph"><div style="max-width:860px;margin:0 auto">
<h1>About {NAME}</h1>
<p>Independent resource for office managers researching bulk snack delivery.</p>
</div></div>
<div class="section" style="max-width:860px">
<h2 style="color:#14532d;margin-bottom:1rem">What This Site Is</h2>
<p>{NAME} is an independent affiliate resource helping office managers, HR professionals, and facilities teams find the best bulk snack delivery for their offices. We focus on Green Rabbit products via Warehouse115 — a leading wholesale bulk snack supplier for US businesses.</p>
<h2 style="color:#14532d;margin:2rem 0 1rem">Affiliate Disclosure</h2>
<p>This site earns commissions through the Warehouse115 / Green Rabbit affiliate programme. When you purchase through our links, we earn a small commission at no extra cost to you. Our recommendations are based on genuine assessment of product quality and value.</p>
<h2 style="color:#14532d;margin:2rem 0 1rem">Contact Warehouse115</h2>
<p>Phone: 678-961-4606 (M-F 8am-5pm EST)<br>
<a href="{AFF_HOME}" rel="noopener">warehouse115.com/green-rabbit.html</a></p>
</div>
{footer()}{JS}</body></html>"""
    (out_dir / "about.html").write_text(about_html, encoding="utf-8")

    guide_links = "".join(
        f'<li><a href="{SITE}/guides/{slug}/">{kw}</a></li>'
        for slug,kw,cat,vol in GENERAL_KW[:30]
    )
    guides_html = f"""<!DOCTYPE html>
<html lang="en"><head>{hd(f"All Guides | {NAME}", "Complete list of office snack delivery guides.", f"{SITE}/guides/")}</head>
<body>{nav()}{trust()}
<div class="ph"><div style="max-width:860px;margin:0 auto">
<h1>Office Snack Guides</h1>
<p>Complete guide library for office managers buying bulk snacks through Green Rabbit at Warehouse115.</p>
</div></div>
<div class="section">
<ul style="columns:2;column-gap:2rem;list-style:none;font-size:.92rem;line-height:2.4">{guide_links}</ul>
</div>
{footer()}{JS}</body></html>"""
    (out_dir / "guides" / "index.html").write_text(guides_html, encoding="utf-8")
    print("  ✓ Essential pages")


# ── SITEMAP + ROBOTS + LLMS ───────────────────────────────────────────────────
def build_sitemap_robots(out_dir, all_urls):
    sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    sm += f'<url><loc>{SITE}/</loc><changefreq>daily</changefreq><priority>1.0</priority></url>\n'
    for url,pri,freq in all_urls:
        sm += f'<url><loc>{url}</loc><changefreq>{freq}</changefreq><priority>{pri}</priority></url>\n'
    sm += '</urlset>'
    (out_dir / "sitemap.xml").write_text(sm, encoding="utf-8")
    robots = f"""User-agent: *
Allow: /
Sitemap: {SITE}/sitemap.xml

User-agent: GPTBot
Allow: /

User-agent: ChatGPT-User
Allow: /

User-agent: Claude-Web
Allow: /

User-agent: anthropic-ai
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: Google-Extended
Allow: /

User-agent: Googlebot
Allow: /

User-agent: Bingbot
Allow: /
"""
    (out_dir / "robots.txt").write_text(robots, encoding="utf-8")
    txt = f"""# {NAME}
> Bulk office snack delivery affiliate resource — Green Rabbit via Warehouse115

## Product
- 425+ bulk snacks: candy, chips, protein bars, drinks, fresh fruit, yogurt
- Free shipping to contiguous 48 US states
- Wholesale pricing, no subscription, no minimum order
- Affiliate link: {AFF}

## Top Products
- Doritos Nacho Cheese 1oz (50-count) $56.99
- RXBAR Protein Bars Assorted (15-count) $57.93
- Clif Bar Variety Pack (24-count) $74.70
- Planters Salted Peanuts (96-count) $56.80
- Arizona Green Tea (24-count) $39.58
- Chobani Greek Yogurt Variety (16-count) $61.74

## Restrictions
Contiguous US only. No Hawaii, Alaska, Puerto Rico.
"""
    (out_dir / "llms.txt").write_text(txt, encoding="utf-8")


# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    import time
    t0 = time.time()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "guides").mkdir(parents=True, exist_ok=True)

    total = len(EN_KEYWORDS)
    print(f"\n{'='*60}")
    print(f"  {NAME} — Full Build")
    print(f"  EN keywords: {total:,} | Blog: {len(BLOG_SEED)}")
    print(f"  Breakdown: General={len(GENERAL_KW)} Cat={len(CAT_KW)} Industry={len(INDUSTRY_KW)}")
    print(f"  Comparison={len(COMPARISON_KW)} Extra={len(EXTRA_KW)} State={len(STATE_KW)} City={len(CITY_KW)}")
    print(f"  Target: ~{total+len(BLOG_SEED)+8:,} pages")
    print(f"{'='*60}")

    build_og(OUT)
    blog_posts = build_blog(OUT)
    build_home(OUT)
    build_essentials(OUT)

    all_urls = []
    for sl,ti,tg,url in blog_posts:
        all_urls.append((url, "0.7", "weekly"))
    all_urls.append((f"{SITE}/blog/", "0.8", "daily"))
    all_urls.append((f"{SITE}/about.html", "0.3", "monthly"))
    all_urls.append((f"{SITE}/guides/", "0.8", "weekly"))

    count = 0
    for idx,(slug, kw_title, category, volume) in enumerate(EN_KEYWORDS):
        d = OUT / "guides" / slug
        d.mkdir(parents=True, exist_ok=True)
        html = kw_page(slug, kw_title, category, volume, idx)
        (d / "index.html").write_text(html, encoding="utf-8")
        pri = "0.9" if category in ("General","Products") else ("0.8" if "Geo" not in category else "0.7")
        all_urls.append((f"{SITE}/guides/{slug}/", pri, "weekly"))
        count += 1
        if count % 200 == 0:
            print(f"  {count}/{total} pages...")

    build_sitemap_robots(OUT, all_urls)

    elapsed = time.time() - t0
    total_pages = count + len(blog_posts) + 6
    print(f"\n{'='*60}")
    print(f"  BUILD COMPLETE in {elapsed:.0f}s")
    print(f"  TOTAL PAGES       : {total_pages:,}")
    print(f"  Sitemap URLs      : {len(all_urls)+1:,}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
