#!/usr/bin/env python3
"""
Import klasifikací z JSON souboru do DB
Podporuje nový formát s metadaty: {group_id: {is_marketing, sender, subject, count}}
"""

import json
import sqlite3
import sys
from datetime import datetime

DB_PATH = '/Users/m.a.j.puzik/apps/maj-subscriptions-local/data/subscriptions.db'

def save_classification(group_id: int, sender: str, subject: str, is_marketing: bool, source: str = 'manual_import'):
    """Uloží klasifikaci do DB"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO email_classifications
        (group_id, sender, subject_pattern, is_marketing, classified_at, source)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (group_id, sender, subject, 1 if is_marketing else 0, datetime.now().isoformat(), source))
    conn.commit()
    conn.close()

def import_from_json(json_file: str):
    """Importuje klasifikace z JSON souboru"""

    print(f"📥 Načítám JSON soubor: {json_file}")

    # Načíst JSON
    with open(json_file, 'r', encoding='utf-8') as f:
        classifications = json.load(f)

    if not classifications:
        print("⚠️  JSON soubor je prázdný")
        return

    print(f"✓ Načteno {len(classifications)} záznamů z JSON")
    print()

    # Import do DB
    imported = 0
    skipped = 0
    errors = 0

    for group_id_str, data in classifications.items():
        try:
            group_id = int(group_id_str)

            # Podporujeme dva formáty:
            # 1. Nový: {group_id: {is_marketing, sender, subject, count}}
            # 2. Starý: {group_id: is_marketing}

            if isinstance(data, dict):
                # Nový formát s metadaty
                is_marketing = data.get('is_marketing', False)
                sender = data.get('sender', 'unknown')
                subject = data.get('subject', 'unknown')
            elif isinstance(data, bool):
                # Starý formát (jen boolean)
                is_marketing = data
                sender = 'unknown'
                subject = 'unknown'
            else:
                print(f"⚠️  Neznámý formát pro group_id {group_id}: {type(data)}")
                skipped += 1
                continue

            # Přeskočit unknown sendery (pravděpodobně chyba)
            if sender == 'unknown' and subject == 'unknown':
                print(f"⚠️  Přeskakuji group_id {group_id} (chybí metadata)")
                skipped += 1
                continue

            # Uložit do DB
            save_classification(group_id, sender, subject, is_marketing, source='manual_import')
            imported += 1

            # Zobraz progress každých 10 záznamů
            if imported % 10 == 0:
                print(f"  Importováno {imported}...")

        except Exception as e:
            print(f"❌ Chyba při importu group_id {group_id_str}: {e}")
            errors += 1
            continue

    print()
    print("="*60)
    print(f"✅ Import dokončen!")
    print(f"  Importováno: {imported}")
    print(f"  Přeskočeno: {skipped}")
    print(f"  Chyby: {errors}")
    print("="*60)
    print()
    print("🔍 Pro ověření spusť:")
    print(f"  sqlite3 {DB_PATH} \"SELECT COUNT(*) FROM email_classifications WHERE source='manual_import'\"")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python3 import_classifications_from_json.py <json_file>")
        print()
        print("Příklad:")
        print("  python3 import_classifications_from_json.py ~/Downloads/marketing_classifications_with_metadata.json")
        sys.exit(1)

    json_file = sys.argv[1]
    import_from_json(json_file)
