import math
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd
import streamlit as st

# ============================================================
# Konfiguration / Defaults
# ============================================================

DEFAULT_CITY = "Leipzig"
DEFAULT_MAX_PRICE = 250000
DEFAULT_MIN_AREA = 70
DEFAULT_EQUITY = 100000
DEFAULT_INTEREST = 3.8          # Sollzins p.a.
DEFAULT_REPAYMENT = 2.0         # anfängliche Tilgung p.a.
DEFAULT_NON_ALLOCABLE_RATIO = 0.25   # nicht umlagefähiger Anteil vom Hausgeld
DEFAULT_VACANCY_RATIO = 0.03         # Mietausfallwagnis
DEFAULT_MAINTENANCE_PER_M2_YEAR = 12 # grobe Instandhaltung
DEFAULT_MIN_ROOMS = 2.5

# Beispielwerte für Lage- und Mietniveau.
# Diese Werte sind bewusst heuristisch und sollen später mit echten Marktdaten verfeinert werden.
LEIPZIG_DISTRICT_DATA = {
    "Zentrum":               {"rent": 14.5, "location_score": 10},
    "Zentrum-Süd":           {"rent": 14.0, "location_score": 10},
    "Zentrum-Ost":           {"rent": 13.5, "location_score": 9},
    "Zentrum-Nordwest":      {"rent": 13.5, "location_score": 9},
    "Südvorstadt":           {"rent": 13.8, "location_score": 10},
    "Schleußig":             {"rent": 13.8, "location_score": 10},
    "Plagwitz":              {"rent": 13.4, "location_score": 9},
    "Lindenau":              {"rent": 12.6, "location_score": 8},
    "Gohlis-Süd":            {"rent": 13.2, "location_score": 9},
    "Gohlis-Mitte":          {"rent": 12.8, "location_score": 8},
    "Gohlis-Nord":           {"rent": 12.1, "location_score": 7},
    "Reudnitz-Thonberg":     {"rent": 12.0, "location_score": 7},
    "Stötteritz":            {"rent": 11.9, "location_score": 7},
    "Connewitz":             {"rent": 13.0, "location_score": 9},
    "Leutzsch":              {"rent": 11.3, "location_score": 6},
    "Mockau":                {"rent": 10.7, "location_score": 5},
    "Paunsdorf":             {"rent": 10.4, "location_score": 5},
    "Grünau":                {"rent": 9.6,  "location_score": 4},
    "Sellerhausen-Stünz":    {"rent": 10.9, "location_score": 6},
    "Möckern":               {"rent": 11.8, "location_score": 7},
    "Altlindenau":           {"rent": 12.7, "location_score": 8},
    "Kleinzschocher":        {"rent": 11.4, "location_score": 6},
    "Anger-Crottendorf":     {"rent": 11.2, "location_score": 6},
    "Eutritzsch":            {"rent": 11.8, "location_score": 7},
}

DEFAULT_DISTRICT = {
    "rent": 11.5,
    "location_score": 6,
}

# ============================================================
# Beispiel-Datenquelle
# ============================================================
# Diese Testdaten ersetzen vorerst eine echte API / ein Portal.
# Später kann fetch_listings() gegen eine API oder ein zulässiges Importformat getauscht werden.

SAMPLE_LISTINGS = [
    {
        "id": "L001",
        "title": "3-Zimmer-Wohnung in Schleußig",
        "city": "Leipzig",
        "district": "Schleußig",
        "address": "Nahe König-Albert-Brücke",
        "price_eur": 239000,
        "area_m2": 78,
        "rooms": 3,
        "floor": 2,
        "year_built": 1998,
        "house_fee_eur": 290,
        "parking": False,
        "balcony": True,
        "rented": False,
        "url": "https://example.com/expose/L001",
    },
    {
        "id": "L002",
        "title": "Kapitalanlage in Gohlis-Süd",
        "city": "Leipzig",
        "district": "Gohlis-Süd",
        "address": "Ruhige Seitenstraße",
        "price_eur": 248000,
        "area_m2": 82,
        "rooms": 3,
        "floor": 1,
        "year_built": 2005,
        "house_fee_eur": 260,
        "parking": True,
        "balcony": True,
        "rented": True,
        "current_rent_eur": 910,
        "url": "https://example.com/expose/L002",
    },
    {
        "id": "L003",
        "title": "Große 2,5-Zimmer-Wohnung in Lindenau",
        "city": "Leipzig",
        "district": "Lindenau",
        "address": "Altbau nahe Karl-Heine-Straße",
        "price_eur": 219000,
        "area_m2": 74,
        "rooms": 2.5,
        "floor": 3,
        "year_built": 1910,
        "house_fee_eur": 310,
        "parking": False,
        "balcony": True,
        "rented": False,
        "url": "https://example.com/expose/L003",
    },
    {
        "id": "L004",
        "title": "4-Zimmer-Wohnung in Reudnitz",
        "city": "Leipzig",
        "district": "Reudnitz-Thonberg",
        "address": "Nahe Lene-Voigt-Park",
        "price_eur": 255000,
        "area_m2": 87,
        "rooms": 4,
        "floor": 4,
        "year_built": 1935,
        "house_fee_eur": 355,
        "parking": False,
        "balcony": False,
        "rented": False,
        "url": "https://example.com/expose/L004",
    },
    {
        "id": "L005",
        "title": "3-Zimmer in Stötteritz mit Balkon",
        "city": "Leipzig",
        "district": "Stötteritz",
        "address": "Familienfreundliche Lage",
        "price_eur": 228000,
        "area_m2": 76,
        "rooms": 3,
        "floor": 2,
        "year_built": 2001,
        "house_fee_eur": 245,
        "parking": True,
        "balcony": True,
        "rented": False,
        "url": "https://example.com/expose/L005",
    },
]

# ============================================================
# Helper
# ============================================================

def district_profile(district: str) -> Dict[str, Any]:
    return LEIPZIG_DISTRICT_DATA.get(district, DEFAULT_DISTRICT)


def safe_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return default


def price_per_m2(price_eur: float, area_m2: float) -> Optional[float]:
    if area_m2 <= 0:
        return None
    return price_eur / area_m2


def monthly_annuity_payment(loan_amount: float, annual_interest_pct: float, annual_repayment_pct: float) -> float:
    """
    Vereinfachtes Modell:
    Annuität = Darlehen * (Sollzins + anfängliche Tilgung) / 12
    """
    if loan_amount <= 0:
        return 0.0
    annuity_rate = (annual_interest_pct + annual_repayment_pct) / 100.0
    return loan_amount * annuity_rate / 12.0


def estimated_market_rent_eur(area_m2: float, district: str) -> float:
    rent_per_m2 = district_profile(district)["rent"]
    return area_m2 * rent_per_m2


def annual_gross_rent(monthly_rent: float) -> float:
    return monthly_rent * 12.0


def annual_vacancy_cost(monthly_rent: float, vacancy_ratio: float) -> float:
    return annual_gross_rent(monthly_rent) * vacancy_ratio


def annual_non_allocable_house_fee(house_fee_monthly: float, non_allocable_ratio: float) -> float:
    return house_fee_monthly * 12.0 * non_allocable_ratio


def annual_maintenance(area_m2: float, maintenance_per_m2_year: float) -> float:
    return area_m2 * maintenance_per_m2_year


def annual_net_operating_income(
    monthly_rent: float,
    house_fee_monthly: float,
    area_m2: float,
    non_allocable_ratio: float,
    vacancy_ratio: float,
    maintenance_per_m2_year: float,
) -> float:
    gross = annual_gross_rent(monthly_rent)
    vacancy = annual_vacancy_cost(monthly_rent, vacancy_ratio)
    non_allocable_fee = annual_non_allocable_house_fee(house_fee_monthly, non_allocable_ratio)
    maintenance = annual_maintenance(area_m2, maintenance_per_m2_year)
    return gross - vacancy - non_allocable_fee - maintenance


def gross_yield_pct(price_eur: float, monthly_rent: float) -> float:
    if price_eur <= 0:
        return 0.0
    return annual_gross_rent(monthly_rent) / price_eur * 100.0


def net_yield_pct(price_eur: float, annual_noi: float) -> float:
    if price_eur <= 0:
        return 0.0
    return annual_noi / price_eur * 100.0


def monthly_cashflow_before_tax(
    monthly_rent: float,
    monthly_debt_service: float,
    house_fee_monthly: float,
    area_m2: float,
    non_allocable_ratio: float,
    vacancy_ratio: float,
    maintenance_per_m2_year: float,
) -> float:
    annual_noi = annual_net_operating_income(
        monthly_rent=monthly_rent,
        house_fee_monthly=house_fee_monthly,
        area_m2=area_m2,
        non_allocable_ratio=non_allocable_ratio,
        vacancy_ratio=vacancy_ratio,
        maintenance_per_m2_year=maintenance_per_m2_year,
    )
    return annual_noi / 12.0 - monthly_debt_service


def payback_years_equity(equity: float, monthly_cashflow: float) -> Optional[float]:
    """
    Sehr grobe Kennzahl:
    Wie lange dauert es, bis das eingesetzte Eigenkapital allein aus dem freien Cashflow wieder hereinkommt?
    """
    annual_cashflow = monthly_cashflow * 12.0
    if annual_cashflow <= 0:
        return None
    return equity / annual_cashflow


def score_listing(
    item: Dict[str, Any],
    monthly_rent: float,
    monthly_debt_service: float,
    monthly_cashflow: float,
    ppsqm: float,
    annual_noi: float,
) -> Dict[str, Any]:
    score = 0
    reasons: List[str] = []

    district = item.get("district", "")
    loc = district_profile(district)
    loc_score = safe_float(loc.get("location_score", 6))

    # Lage
    score += int(loc_score * 5)
    reasons.append(f"+{int(loc_score * 5)} Lage {district}")

    # Größe
    area = safe_float(item.get("area_m2"))
    if area >= 85:
        score += 14
        reasons.append("+14 große Fläche")
    elif area >= 75:
        score += 10
        reasons.append("+10 passende Fläche")
    elif area >= 70:
        score += 7
        reasons.append("+7 Mindestgröße erfüllt")
    else:
        score -= 15
        reasons.append("-15 zu klein")

    # Zimmer
    rooms = safe_float(item.get("rooms"))
    if 2.5 <= rooms <= 4.0:
        score += 8
        reasons.append("+8 gute Vermietbarkeit Zimmerzahl")

    # Preis
    price = safe_float(item.get("price_eur"))
    if price <= 230000:
        score += 12
        reasons.append("+12 unter Zielbudget")
    elif price <= 250000:
        score += 7
        reasons.append("+7 im Zielbudget")
    elif price <= 265000:
        score -= 3
        reasons.append("-3 leicht über Budget")
    else:
        score -= 12
        reasons.append("-12 deutlich über Budget")

    # Preis pro m²
    if ppsqm <= 2800:
        score += 12
        reasons.append("+12 günstiger m²-Preis")
    elif ppsqm <= 3300:
        score += 5
        reasons.append("+5 akzeptabler m²-Preis")
    elif ppsqm <= 3800:
        score -= 4
        reasons.append("-4 ambitionierter m²-Preis")
    else:
        score -= 12
        reasons.append("-12 hoher m²-Preis")

    # Cashflow
    if monthly_cashflow >= 150:
        score += 18
        reasons.append("+18 sehr guter Cashflow")
    elif monthly_cashflow >= 0:
        score += 10
        reasons.append("+10 mindestens selbsttragend")
    elif monthly_cashflow >= -150:
        score += 2
        reasons.append("+2 nahe an Selbstfinanzierung")
    elif monthly_cashflow >= -300:
        score -= 8
        reasons.append("-8 spürbar negativer Cashflow")
    else:
        score -= 18
        reasons.append("-18 klar negativer Cashflow")

    # Rendite
    net_yield = net_yield_pct(price, annual_noi)
    if net_yield >= 4.5:
        score += 12
        reasons.append("+12 starke Nettorendite")
    elif net_yield >= 3.8:
        score += 6
        reasons.append("+6 solide Nettorendite")
    elif net_yield < 3.0:
        score -= 8
        reasons.append("-8 schwache Nettorendite")

    # Merkmale
    if item.get("balcony"):
        score += 4
        reasons.append("+4 Balkon")
    if item.get("parking"):
        score += 3
        reasons.append("+3 Stellplatz")
    if item.get("rented"):
        score += 2
        reasons.append("+2 bereits vermietet")

    # Baujahr grob
    year_built = safe_float(item.get("year_built"), 0)
    if year_built >= 1995:
        score += 4
        reasons.append("+4 jüngeres Baujahr")
    elif year_built > 0 and year_built < 1920:
        score -= 2
        reasons.append("-2 Altbau-Risiko / CAPEX prüfen")

    return {
        "score": score,
        "score_reasons": reasons,
        "location_score": loc_score,
        "net_yield_pct": net_yield,
    }


# ============================================================
# Datenbeschaffung
# ============================================================

@st.cache_data(show_spinner=False)
def fetch_listings() -> List[Dict[str, Any]]:
    """
    Platzhalter für echte Datenquelle.

    Später kann hier z.B. umgesetzt werden:
    - Import aus CSV / Excel
    - Abfrage einer API
    - Einlesen eines JSON-Feeds
    - Portal-spezifischer Adapter (nur wenn rechtlich/technisch zulässig)
    """
    return SAMPLE_LISTINGS


def enrich_listing(
    item: Dict[str, Any],
    equity_eur: float,
    annual_interest_pct: float,
    annual_repayment_pct: float,
    non_allocable_ratio: float,
    vacancy_ratio: float,
    maintenance_per_m2_year: float,
) -> Dict[str, Any]:
    price = safe_float(item.get("price_eur"))
    area = safe_float(item.get("area_m2"))
    house_fee = safe_float(item.get("house_fee_eur"))
    district = item.get("district", "")

    loan_amount = max(0.0, price - equity_eur)
    ppsqm = price_per_m2(price, area) or 0.0

    # Falls bereits vermietet und Miete angegeben, diese bevorzugen.
    current_rent = safe_float(item.get("current_rent_eur"), 0.0)
    est_rent = estimated_market_rent_eur(area, district)
    monthly_rent = current_rent if current_rent > 0 else est_rent

    debt_service = monthly_annuity_payment(
        loan_amount=loan_amount,
        annual_interest_pct=annual_interest_pct,
        annual_repayment_pct=annual_repayment_pct,
    )

    annual_noi = annual_net_operating_income(
        monthly_rent=monthly_rent,
        house_fee_monthly=house_fee,
        area_m2=area,
        non_allocable_ratio=non_allocable_ratio,
        vacancy_ratio=vacancy_ratio,
        maintenance_per_m2_year=maintenance_per_m2_year,
    )

    monthly_cf = monthly_cashflow_before_tax(
        monthly_rent=monthly_rent,
        monthly_debt_service=debt_service,
        house_fee_monthly=house_fee,
        area_m2=area,
        non_allocable_ratio=non_allocable_ratio,
        vacancy_ratio=vacancy_ratio,
        maintenance_per_m2_year=maintenance_per_m2_year,
    )

    payback = payback_years_equity(equity_eur, monthly_cf)
    score_data = score_listing(
        item=item,
        monthly_rent=monthly_rent,
        monthly_debt_service=debt_service,
        monthly_cashflow=monthly_cf,
        ppsqm=ppsqm,
        annual_noi=annual_noi,
    )

    item["_price_per_m2"] = ppsqm
    item["_estimated_rent_eur"] = monthly_rent
    item["_loan_amount_eur"] = loan_amount
    item["_monthly_debt_service_eur"] = debt_service
    item["_annual_noi_eur"] = annual_noi
    item["_gross_yield_pct"] = gross_yield_pct(price, monthly_rent)
    item["_net_yield_pct"] = score_data["net_yield_pct"]
    item["_monthly_cashflow_eur"] = monthly_cf
    item["_equity_payback_years"] = payback
    item["_location_score"] = score_data["location_score"]
    item["_score"] = score_data["score"]
    item["_score_reasons"] = score_data["score_reasons"]
    item["_rent_source"] = "Ist-Miete" if current_rent > 0 else "Marktmiete geschätzt"

    return item


# ============================================================
# Filter / UI
# ============================================================

def filter_listings(
    items: List[Dict[str, Any]],
    city: str,
    max_price_eur: float,
    min_area_m2: float,
    min_rooms: float,
    only_leipzig: bool = True,
) -> List[Dict[str, Any]]:
    out = []
    for item in items:
        item_city = str(item.get("city", "")).strip().lower()
        price = safe_float(item.get("price_eur"))
        area = safe_float(item.get("area_m2"))
        rooms = safe_float(item.get("rooms"))

        if only_leipzig and item_city != city.strip().lower():
            continue
        if price > max_price_eur:
            continue
        if area < min_area_m2:
            continue
        if rooms < min_rooms:
            continue

        out.append(item)
    return out


def render_metric_grid(item: Dict[str, Any]) -> None:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Preis", f"{item['price_eur']:,.0f} €".replace(",", "."))
    c2.metric("Fläche", f"{item['area_m2']:.1f} m²")
    c3.metric("m²-Preis", f"{item['_price_per_m2']:,.0f} €/m²".replace(",", "."))
    c4.metric("Score", f"{int(item['_score'])}")

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Soll-Miete", f"{item['_estimated_rent_eur']:,.0f} €/Monat".replace(",", "."))
    c6.metric("Rate", f"{item['_monthly_debt_service_eur']:,.0f} €/Monat".replace(",", "."))
    c7.metric("Cashflow", f"{item['_monthly_cashflow_eur']:,.0f} €/Monat".replace(",", "."))
    c8.metric("Nettorendite", f"{item['_net_yield_pct']:.2f} %")


def render_listing_card(item: Dict[str, Any]) -> None:
    district = item.get("district", "—")
    address = item.get("address", "—")
    rent_source = item.get("_rent_source", "")
    payback = item.get("_equity_payback_years")

    badge = "🟢"
    if item["_monthly_cashflow_eur"] < -150:
        badge = "🔴"
    elif item["_monthly_cashflow_eur"] < 0:
        badge = "🟡"

    title = f"{badge} {item.get('title', 'Wohnung')} · {district}"

    with st.expander(title, expanded=False):
        st.write(f"**Adresse:** {address}")
        st.write(
            f"**Zimmer:** {item.get('rooms', '—')} · "
            f"**Baujahr:** {item.get('year_built', '—')} · "
            f"**Hausgeld:** {item.get('house_fee_eur', '—')} €/Monat"
        )

        flags = []
        if item.get("balcony"):
            flags.append("Balkon")
        if item.get("parking"):
            flags.append("Stellplatz")
        if item.get("rented"):
            flags.append("vermietet")

        if flags:
            st.write("**Merkmale:** " + " · ".join(flags))

        render_metric_grid(item)

        st.write(
            f"**Mieteingang:** {item['_estimated_rent_eur']:,.0f} €/Monat "
            f"({rent_source})".replace(",", ".")
        )

        st.write(
            f"**Bruttorendite:** {item['_gross_yield_pct']:.2f} % · "
            f"**NOI p.a.:** {item['_annual_noi_eur']:,.0f} €".replace(",", ".")
        )

        if payback is None:
            st.write("**Eigenkapital-Rückfluss:** mit aktuellem Cashflow nicht darstellbar")
        else:
            st.write(f"**Eigenkapital-Rückfluss grob:** {payback:.1f} Jahre")

        st.write("**Score-Treiber:**")
        for reason in item["_score_reasons"]:
            st.write(f"- {reason}")

        if item.get("url"):
            st.markdown(f"[Exposé öffnen]({item['url']})")


# ============================================================
# App
# ============================================================

st.set_page_config(page_title="WohnungsWatch Leipzig", layout="wide")

st.title("🏢 WohnungsWatch Leipzig")
st.caption("Kapitalanlage-Check für Eigentumswohnungen in Leipzig")

with st.sidebar:
    st.header("Einstellungen")

    city = st.text_input("Stadt", value=DEFAULT_CITY)
    max_price_eur = st.number_input("Max. Kaufpreis (€)", min_value=50000, max_value=1000000, value=DEFAULT_MAX_PRICE, step=5000)
    min_area_m2 = st.number_input("Min. Wohnfläche (m²)", min_value=30, max_value=200, value=DEFAULT_MIN_AREA, step=1)
    min_rooms = st.number_input("Min. Zimmer", min_value=1.0, max_value=8.0, value=float(DEFAULT_MIN_ROOMS), step=0.5)

    st.divider()
    st.subheader("Finanzierung")
    equity_eur = st.number_input("Eigenkapital (€)", min_value=0, max_value=1000000, value=DEFAULT_EQUITY, step=5000)
    annual_interest_pct = st.number_input("Sollzins p.a. (%)", min_value=0.0, max_value=15.0, value=float(DEFAULT_INTEREST), step=0.1)
    annual_repayment_pct = st.number_input("Anfängliche Tilgung p.a. (%)", min_value=0.0, max_value=10.0, value=float(DEFAULT_REPAYMENT), step=0.1)

    st.divider()
    st.subheader("Bewertungsannahmen")
    non_allocable_ratio = st.slider("Nicht umlagefähiger Hausgeld-Anteil", min_value=0.0, max_value=0.6, value=float(DEFAULT_NON_ALLOCABLE_RATIO), step=0.01)
    vacancy_ratio = st.slider("Mietausfallwagnis", min_value=0.0, max_value=0.15, value=float(DEFAULT_VACANCY_RATIO), step=0.01)
    maintenance_per_m2_year = st.number_input("Instandhaltung (€ pro m²/Jahr)", min_value=0.0, max_value=50.0, value=float(DEFAULT_MAINTENANCE_PER_M2_YEAR), step=1.0)

    sort_mode = st.selectbox(
        "Sortierung",
        ["Score", "Cashflow", "Nettorendite", "Kaufpreis", "Preis pro m²"],
        index=0,
    )

items = fetch_listings()

items = filter_listings(
    items=items,
    city=city,
    max_price_eur=max_price_eur,
    min_area_m2=min_area_m2,
    min_rooms=min_rooms,
    only_leipzig=True,
)

items = [
    enrich_listing(
        item=dict(item),
        equity_eur=equity_eur,
        annual_interest_pct=annual_interest_pct,
        annual_repayment_pct=annual_repayment_pct,
        non_allocable_ratio=non_allocable_ratio,
        vacancy_ratio=vacancy_ratio,
        maintenance_per_m2_year=maintenance_per_m2_year,
    )
    for item in items
]

if sort_mode == "Score":
    items = sorted(items, key=lambda x: (-x["_score"], -x["_monthly_cashflow_eur"]))
elif sort_mode == "Cashflow":
    items = sorted(items, key=lambda x: (-x["_monthly_cashflow_eur"], -x["_score"]))
elif sort_mode == "Nettorendite":
    items = sorted(items, key=lambda x: (-x["_net_yield_pct"], -x["_score"]))
elif sort_mode == "Kaufpreis":
    items = sorted(items, key=lambda x: x["price_eur"])
elif sort_mode == "Preis pro m²":
    items = sorted(items, key=lambda x: x["_price_per_m2"])

top_items = items[:5]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Treffer", len(items))
col2.metric("Budget", f"{max_price_eur:,.0f} €".replace(",", "."))
col3.metric("Eigenkapital", f"{equity_eur:,.0f} €".replace(",", "."))
col4.metric("Stand", datetime.now().strftime("%d.%m.%Y %H:%M"))

st.divider()

st.subheader("⭐ Beste Anlagekandidaten")
if top_items:
    for idx, item in enumerate(top_items, start=1):
        st.markdown(
            f"**{idx}. {item['title']}** — {item['district']} · "
            f"Score {item['_score']} · "
            f"Cashflow {item['_monthly_cashflow_eur']:,.0f} €/Monat · "
            f"Nettorendite {item['_net_yield_pct']:.2f} %".replace(",", ".")
        )
else:
    st.info("Keine Treffer mit den aktuellen Filtern.")

st.divider()

st.subheader("📋 Ergebnisliste")
if not items:
    st.warning("Keine Wohnungen gefunden. Filter lockern oder Datenquelle erweitern.")
else:
    for item in items:
        render_listing_card(item)

    df = pd.DataFrame([
        {
            "Titel": x["title"],
            "Stadtteil": x["district"],
            "Preis €": x["price_eur"],
            "Fläche m²": x["area_m2"],
            "Zimmer": x["rooms"],
            "€/m²": round(x["_price_per_m2"], 0),
            "Miete €/Monat": round(x["_estimated_rent_eur"], 0),
            "Rate €/Monat": round(x["_monthly_debt_service_eur"], 0),
            "Cashflow €/Monat": round(x["_monthly_cashflow_eur"], 0),
            "Bruttorendite %": round(x["_gross_yield_pct"], 2),
            "Nettorendite %": round(x["_net_yield_pct"], 2),
            "Score": int(x["_score"]),
        }
        for x in items
    ])

    st.download_button(
        "⬇️ Ergebnisliste als CSV",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name="wohnungswatch_leipzig.csv",
        mime="text/csv",
    )
