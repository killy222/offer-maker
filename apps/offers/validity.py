"""Stored `Offer.validity_label` values are Bulgarian; API and UI use these exact strings."""

MIGRATE_EN_TO_BG = {
    "": "",
    "7 days": "7 дни",
    "14 days": "14 дни",
    "30 days": "30 дни",
    "60 days": "60 дни",
}

VALIDITY_7 = "7 дни"
VALIDITY_14 = "14 дни"
VALIDITY_30 = "30 дни"
VALIDITY_60 = "60 дни"

MIGRATE_BG_TO_EN = {bg: en for en, bg in MIGRATE_EN_TO_BG.items() if en and bg}
