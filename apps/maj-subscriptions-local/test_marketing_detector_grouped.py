#!/usr/bin/env python3
"""
Marketing Email Detector - Grouped Test (Ultra Compact)
Seskupuje podobné emaily a umožňuje klasifikaci celé skupiny
+ Automatická klasifikace TOP 5 skupin
+ Default zobrazení: jen neklasifikované
"""

import sqlite3
import json
from typing import List, Dict, Any
from collections import defaultdict
from difflib import SequenceMatcher
from datetime import datetime
from marketing_email_detector import MarketingEmailDetector

DB_PATH = '/Users/m.a.j.puzik/apps/maj-subscriptions-local/data/subscriptions.db'

def similar(a: str, b: str, threshold: float = 0.8) -> bool:
    """Porovná podobnost dvou stringů"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio() >= threshold

def has_subscription_keywords(subject: str, body: str) -> bool:
    """Detekuje subscription-related emaily"""
    text = (subject + ' ' + body).lower()
    keywords = [
        'abo', 'abonnement', 'subscription', 'předplatné', 'predplatne',
        'membership', 'členství', 'clenstvi', 'renewal', 'obnovení', 'obnoveni',
        'payment confirmation', 'potvrzení platby', 'potvrzeni platby',
        'invoice', 'faktura', 'receipt', 'účtenka', 'uctenka'
    ]
    return any(kw in text for kw in keywords)

def normalize_subject(subject: str) -> str:
    """Normalizuje subject pro grouping"""
    # Odstranění běžných variací
    import re
    s = subject.lower()
    # Odstranění dat
    s = re.sub(r'\d{1,2}[./\-]\d{1,2}[./\-]\d{2,4}', '', s)
    # Odstranění čísel
    s = re.sub(r'\b\d+\b', '', s)
    # Odstranění extra mezer
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def init_db():
    """Vytvoří tabulku pro klasifikace"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS email_classifications (
            group_id INTEGER PRIMARY KEY,
            sender TEXT,
            subject_pattern TEXT,
            is_marketing INTEGER,
            classified_at TEXT,
            source TEXT
        )
    """)

    conn.commit()
    conn.close()

def save_classification(group_id: int, sender: str, subject: str, is_marketing: bool, source: str = 'manual'):
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

def load_classifications() -> Dict[int, bool]:
    """Načte klasifikace z DB"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT group_id, is_marketing FROM email_classifications")
        classifications = {row[0]: bool(row[1]) for row in cursor.fetchall()}
    except sqlite3.OperationalError:
        # Tabulka neexistuje
        classifications = {}

    conn.close()
    return classifications

def load_sender_classifications() -> Dict[str, bool]:
    """Načte klasifikace podle sendera (pro smart matching)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT sender, is_marketing FROM email_classifications")
        # Normalizovat sender na lowercase
        sender_map = {row[0].lower().strip(): bool(row[1]) for row in cursor.fetchall()}
    except sqlite3.OperationalError:
        sender_map = {}

    conn.close()
    return sender_map

def apply_sender_classification(groups: List[Dict], sender_map: Dict[str, bool]) -> int:
    """Aplikuje klasifikaci na skupiny podle senderu"""
    applied_count = 0

    for group in groups:
        sender_normalized = group['from'].lower().strip()

        # Zkusit přesnou shodu
        if sender_normalized in sender_map:
            # Uložit do DB s novým group_id
            save_classification(
                group['id'],
                group['from'],
                group['subject_normalized'],
                sender_map[sender_normalized],
                source='sender_match'
            )
            applied_count += 1
            continue

        # Zkusit partial match (pokud DB sender obsahuje aktuální sender nebo naopak)
        for db_sender, is_marketing in sender_map.items():
            # Extract email část
            db_email = db_sender.split('<')[-1].strip('>').strip().lower() if '<' in db_sender else db_sender
            current_email = sender_normalized.split('<')[-1].strip('>').strip().lower() if '<' in sender_normalized else sender_normalized

            if db_email and current_email and (db_email in current_email or current_email in db_email):
                save_classification(
                    group['id'],
                    group['from'],
                    group['subject_normalized'],
                    is_marketing,
                    source='sender_partial_match'
                )
                applied_count += 1
                break

    return applied_count

def auto_classify_top_groups(groups: List[Dict], existing_classifications: Dict[int, bool]) -> int:
    """Automaticky klasifikuje TOP 5 nejčastější skupiny jako marketing (jen neklasifikované)"""

    # Definice TOP senderů (z původního požadavku)
    top_patterns = [
        'mobile.de',
        'autoscout24',
        'immowelt'
    ]

    classified_count = 0

    for group in groups:
        # Přeskočit, pokud už je klasifikovaná
        if group['id'] in existing_classifications:
            continue

        sender_lower = group['from'].lower()

        # Kontrola jestli sender obsahuje některý z TOP patterns
        for pattern in top_patterns:
            if pattern in sender_lower:
                # Uložit do DB
                save_classification(
                    group['id'],
                    group['from'],
                    group['subject_normalized'],
                    is_marketing=True,
                    source='auto'
                )
                classified_count += 1
                break

    return classified_count

def group_emails(emails: List[Dict]) -> List[Dict]:
    """Seskupí podobné emaily - lepší logika"""
    groups = []
    used = set()

    for i, email in enumerate(emails):
        if i in used:
            continue

        # Zjistit jestli má subscription keywords
        has_sub_keywords = has_subscription_keywords(email['subject'], email['body'])

        # Vytvořit novou skupinu
        group = {
            'id': len(groups),
            'from': email['from'],
            'subject_normalized': normalize_subject(email['subject']),
            'subject_example': email['subject'][:60],
            'emails': [email],
            'count': 1,
            'has_subscription': has_sub_keywords
        }
        used.add(i)

        # Najít podobné emaily - POUZE stejný odesílatel
        for j, other in enumerate(emails[i+1:], start=i+1):
            if j in used:
                continue

            # Musí být stejný odesílatel
            same_from = email['from'] == other['from']

            # Pro subscription emaily - musí také obsahovat subscription keywords
            other_has_sub = has_subscription_keywords(other['subject'], other['body'])

            # Pokud je to subscription email, seskupit jen s jinými subscription emaily od stejného odesílatele
            if has_sub_keywords:
                if same_from and other_has_sub:
                    group['emails'].append(other)
                    group['count'] += 1
                    used.add(j)
            else:
                # Pro běžné marketing emaily - stačí stejný odesílatel
                if same_from:
                    group['emails'].append(other)
                    group['count'] += 1
                    used.add(j)

        groups.append(group)

    # Seřadit - subscription emaily nahoře, pak podle počtu
    groups.sort(key=lambda g: (not g['has_subscription'], -g['count']))

    return groups

def load_emails(limit: int = 5000) -> List[Dict]:
    """Načte emaily z databáze"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT email_subject, email_from, email_body_compact, email_body_full, email_date
        FROM email_evidence
        ORDER BY email_date DESC
        LIMIT ?
    """, (limit,))

    emails = []
    for row in cursor.fetchall():
        emails.append({
            'subject': row[0] or '',
            'from': row[1] or '',
            'body': row[2] or '',
            'html_body': row[3] or '',
            'date': row[4] or ''
        })

    conn.close()
    return emails

def analyze_groups(groups: List[Dict]) -> List[Dict]:
    """Analyzuje skupiny emailů"""
    detector = MarketingEmailDetector()

    for group in groups:
        # Analyzuj první email ze skupiny jako reprezentanta
        email = group['emails'][0]
        is_marketing, confidence, details = detector.analyze(email)

        group['is_marketing'] = is_marketing
        group['confidence'] = confidence
        group['reasons'] = details['reasons'][:2]  # Max 2 důvody

    return groups

def generate_html(groups: List[Dict], stats: Dict, db_classifications: Dict[int, bool]) -> str:
    """Generuje ultra-kompaktní HTML s předklasifikovanými skupinami"""

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Marketing Groups - {len(groups)} skupin</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Monaco', 'Courier New', monospace;
            font-size: 11px;
            background: #1e1e1e;
            color: #d4d4d4;
            padding: 10px;
            line-height: 1.3;
        }}
        .header {{
            background: #252526;
            padding: 10px;
            margin-bottom: 10px;
            border-left: 3px solid #007acc;
        }}
        .header h1 {{
            font-size: 14px;
            color: #007acc;
            margin-bottom: 5px;
        }}
        .stats {{
            font-size: 10px;
            color: #858585;
        }}
        .controls {{
            background: #252526;
            padding: 8px;
            margin-bottom: 10px;
            display: flex;
            gap: 10px;
            align-items: center;
        }}
        .controls button {{
            background: #0e639c;
            color: white;
            border: none;
            padding: 4px 8px;
            font-size: 10px;
            cursor: pointer;
            border-radius: 2px;
        }}
        .controls button:hover {{ background: #1177bb; }}
        .controls .export {{ background: #0e7d0e; }}
        .controls .export:hover {{ background: #13a513; }}
        .group {{
            background: #252526;
            border-left: 3px solid #007acc;
            margin-bottom: 5px;
            padding: 6px 8px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .group.marketing {{ border-left-color: #f48771; }}
        .group.not-marketing {{ border-left-color: #73c991; }}
        .group.classified {{
            opacity: 0.7;
        }}
        .status-icon {{
            color: #4ec9b0;
            min-width: 20px;
            font-size: 12px;
            font-weight: bold;
        }}
        .group-id {{
            color: #858585;
            min-width: 35px;
            font-size: 10px;
        }}
        .sub-badge {{
            background: #7c3aed;
            color: white;
            padding: 2px 6px;
            border-radius: 2px;
            font-size: 9px;
            font-weight: bold;
        }}
        .count {{
            background: #3e3e42;
            color: #007acc;
            padding: 2px 6px;
            border-radius: 2px;
            font-weight: bold;
            min-width: 30px;
            text-align: center;
            font-size: 10px;
        }}
        .from {{
            color: #9cdcfe;
            width: 200px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            font-size: 10px;
        }}
        .subject {{
            color: #ce9178;
            flex: 1;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            font-size: 10px;
        }}
        .confidence {{
            color: #4ec9b0;
            min-width: 40px;
            text-align: right;
            font-size: 10px;
        }}
        .confidence.high {{ color: #f48771; }}
        .confidence.low {{ color: #858585; }}
        .ai-verdict {{
            color: #858585;
            font-size: 10px;
            min-width: 110px;
            text-align: left;
            padding-left: 10px;
            border-left: 2px solid #3e3e42;
        }}
        .ai-verdict.marketing {{
            color: #f48771;
            border-left-color: #f48771;
        }}
        .ai-verdict.not-marketing {{
            color: #73c991;
            border-left-color: #73c991;
        }}
        .actions {{
            display: flex;
            gap: 5px;
            min-width: 100px;
        }}
        .actions button {{
            background: #3e3e42;
            color: white;
            border: none;
            padding: 3px 10px;
            cursor: pointer;
            font-size: 10px;
            border-radius: 2px;
            font-weight: bold;
        }}
        .actions .yes {{
            background: #f48771;
        }}
        .actions .yes:hover {{ background: #ff6b54; }}
        .actions .no {{
            background: #73c991;
        }}
        .actions .no:hover {{ background: #89e0a4; }}
        .actions button.selected {{
            outline: 2px solid white;
            outline-offset: 2px;
        }}
        .reasons {{
            color: #858585;
            font-size: 9px;
            margin-left: 45px;
            margin-top: 2px;
        }}
        .filter {{
            display: flex;
            gap: 5px;
        }}
        .filter button {{
            background: #3e3e42;
            padding: 4px 10px;
        }}
        .filter button.active {{
            background: #007acc;
        }}
        .progress {{
            color: #4ec9b0;
            font-size: 10px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Marketing Groups - {len(groups)} skupin</h1>
        <div class="stats">
            Celkem: {stats['total']} | Marketing: {stats['marketing']} ({stats['marketing_pct']:.1f}%) |
            Avg confidence: {stats['avg_confidence']:.1f}% | Skupiny seřazeny podle četnosti
        </div>
    </div>

    <div class="controls">
        <button class="export" onclick="saveProgress()" style="background: #0e7d0e; font-weight: bold;">💾 ULOŽIT</button>
        <div class="filter">
            <button onclick="filterGroups('all')" id="filter-all">All ({len(groups)})</button>
            <button onclick="filterGroups('unclassified')" class="active" id="filter-unclassified">Unclassified</button>
            <button onclick="filterGroups('classified')" id="filter-classified">Classified</button>
            <button onclick="filterGroups('marketing')" id="filter-marketing">Marketing</button>
            <button onclick="filterGroups('not-marketing')" id="filter-not-marketing">Not Marketing</button>
        </div>
        <div class="progress" id="progress">Classified: 0/{len(groups)}</div>
        <button class="export" onclick="exportJSON()">💾 Export JSON</button>
        <button class="export" onclick="exportCSV()">📄 Export CSV</button>
        <button class="export" onclick="regenerateUnclassified()">🔄 Regenerate Unclassified</button>
    </div>

    <div id="groups">
"""

    # Generuj skupiny
    for group in groups:
        conf_class = 'high' if group['confidence'] >= 70 else 'low' if group['confidence'] < 40 else ''
        reasons = ' | '.join(group['reasons'][:2])

        # AI verdict
        ai_verdict_class = 'marketing' if group['is_marketing'] else 'not-marketing'
        ai_verdict_text = 'AI: Marketing' if group['is_marketing'] else 'AI: Not MKT'

        # Escape pro HTML
        from_escaped = group['from'][:30].replace('"', '&quot;').replace("'", '&#39;')
        subject_escaped = group['subject_example'].replace('"', '&quot;').replace("'", '&#39;')

        # Subscription badge
        sub_badge = '<span class="sub-badge">SUB</span>' if group['has_subscription'] else ''

        html += f"""
        <div class="group" data-id="{group['id']}" data-marketing="{str(group['is_marketing']).lower()}" data-ai-marketing="{str(group['is_marketing']).lower()}" data-subscription="{str(group['has_subscription']).lower()}">
            <span class="status-icon" id="status-{group['id']}"></span>
            <span class="group-id">#{group['id']}</span>
            {sub_badge}
            <span class="count">{group['count']}×</span>
            <span class="from" title="{from_escaped}">{from_escaped}</span>
            <span class="subject" title="{subject_escaped}">{subject_escaped[:60]}</span>
            <span class="confidence {conf_class}">{group['confidence']}%</span>
            <span class="ai-verdict {ai_verdict_class}">{ai_verdict_text}</span>
            <div class="actions">
                <button class="yes" data-group-id="{group['id']}">MKT</button>
                <button class="no" data-group-id="{group['id']}">NOT</button>
            </div>
        </div>
        <div class="reasons">{reasons}</div>
"""

    # Připravit groups metadata pro JavaScript (pro export)
    groups_metadata = {}
    for group in groups:
        groups_metadata[group['id']] = {
            'sender': group['from'],
            'subject': group['subject_normalized'],
            'count': group['count']
        }

    html += f"""
    </div>

    <script>
        // Načíst klasifikace z DB (Python předává jako JSON)
        let dbClassifications = {json.dumps(db_classifications)};

        // Groups metadata (pro export s sender info)
        let groupsMetadata = {json.dumps(groups_metadata)};

        // Merge s localStorage (localStorage má přednost)
        let localClassifications = JSON.parse(localStorage.getItem('group_classifications') || '{{}}');
        let classifications = {{...dbClassifications, ...localClassifications}};

        let currentFilter = 'unclassified';  // Default: jen neklasifikované

        // Načíst uložené klasifikace a nastavit event listeners
        window.addEventListener('load', function() {{
            // Načíst uložené klasifikace
            Object.keys(classifications).forEach(id => {{
                applyClassification(parseInt(id), classifications[id]);
            }});
            updateProgress();

            // Aplikovat default filtr
            filterGroups('unclassified');

            // Přidat click handlers k tlačítkům
            document.querySelectorAll('.actions button').forEach(btn => {{
                btn.addEventListener('click', function() {{
                    const groupId = parseInt(this.dataset.groupId);
                    const isMarketing = this.classList.contains('yes');
                    classify(groupId, isMarketing);
                }});
            }});
        }});

        function classify(groupId, isMarketing) {{
            classifications[groupId] = isMarketing;
            localStorage.setItem('group_classifications', JSON.stringify(classifications));
            applyClassification(groupId, isMarketing);
            updateProgress();
        }}

        function applyClassification(groupId, isMarketing) {{
            const group = document.querySelector(`[data-id="${{groupId}}"]`);
            if (!group) return;

            // Zobraz háček
            const statusIcon = document.getElementById(`status-${{groupId}}`);
            if (statusIcon) {{
                statusIcon.textContent = '✓';
            }}

            // Označ tlačítko
            group.querySelectorAll('.actions button').forEach(btn => {{
                btn.classList.remove('selected');
            }});
            const btn = isMarketing ? group.querySelector('.yes') : group.querySelector('.no');
            if (btn) btn.classList.add('selected');

            // Přidej třídu
            group.classList.remove('marketing', 'not-marketing');
            group.classList.add(isMarketing ? 'marketing' : 'not-marketing', 'classified');
        }}

        function filterGroups(filter) {{
            currentFilter = filter;
            const groups = document.querySelectorAll('.group');

            // Update buttons
            document.querySelectorAll('.filter button').forEach(btn => {{
                btn.classList.remove('active');
            }});
            document.getElementById(`filter-${{filter}}`).classList.add('active');

            // Filter groups
            groups.forEach(group => {{
                const id = group.dataset.id;
                const isClassified = classifications.hasOwnProperty(id);
                const isMarketing = classifications[id];

                let show = false;
                if (filter === 'all') show = true;
                else if (filter === 'classified' && isClassified) show = true;
                else if (filter === 'marketing' && isClassified && isMarketing) show = true;
                else if (filter === 'not-marketing' && isClassified && !isMarketing) show = true;
                else if (filter === 'unclassified' && !isClassified) show = true;

                group.style.display = show ? 'flex' : 'none';
                group.nextElementSibling.style.display = show ? 'block' : 'none';
            }});
        }}

        function updateProgress() {{
            const total = document.querySelectorAll('.group').length;
            const classified = Object.keys(classifications).length;
            document.getElementById('progress').textContent = `Classified: ${{classified}}/${{total}}`;
        }}

        function exportJSON() {{
            // Export s kompletními daty (sender, subject, classification)
            const exportData = {{}};
            Object.keys(classifications).forEach(id => {{
                const metadata = groupsMetadata[id] || {{}};
                exportData[id] = {{
                    'is_marketing': classifications[id],
                    'sender': metadata.sender || 'unknown',
                    'subject': metadata.subject || 'unknown',
                    'count': metadata.count || 1
                }};
            }});

            const blob = new Blob([JSON.stringify(exportData, null, 2)], {{type: 'application/json'}});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'marketing_classifications_with_metadata.json';
            a.click();
        }}

        function exportCSV() {{
            let csv = 'Group ID,Count,From,Subject,AI Confidence,Manual Classification\\n';
            document.querySelectorAll('.group').forEach(group => {{
                const id = group.dataset.id;
                const count = group.querySelector('.count').textContent;
                const from = group.querySelector('.from').textContent;
                const subject = group.querySelector('.subject').textContent;
                const confidence = group.querySelector('.confidence').textContent;
                const manual = classifications[id] !== undefined ? (classifications[id] ? 'Marketing' : 'Not Marketing') : 'Unclassified';
                csv += `${{id}},"${{count}}","${{from}}","${{subject}}","${{confidence}}","${{manual}}"\\n`;
            }});

            const blob = new Blob([csv], {{type: 'text/csv'}});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'marketing_classifications_grouped.csv';
            a.click();
        }}

        function saveProgress() {{
            alert(`💾 Uloženo ${{Object.keys(classifications).length}} klasifikací do localStorage!`);
        }}

        function regenerateUnclassified() {{
            const unclassified = [];
            document.querySelectorAll('.group').forEach(group => {{
                const id = group.dataset.id;
                if (!classifications.hasOwnProperty(id)) {{
                    unclassified.push(id);
                }}
            }});

            if (unclassified.length === 0) {{
                alert('✅ Všechny skupiny jsou již klasifikovány!');
                return;
            }}

            if (confirm(`🔄 Regenerovat HTML jen s ${{unclassified.length}} neklasifikovanými skupinami?\\n\\nKlasifikace budou zachovány v localStorage.`)) {{
                // Export unclassified IDs
                localStorage.setItem('unclassified_ids', JSON.stringify(unclassified));
                alert('✅ Seznam neklasifikovaných uložen. Spusť:\\n\\npython3 test_marketing_detector_grouped.py --unclassified');
            }}
        }}
    </script>
</body>
</html>
"""
    return html

def main():
    print("=" * 70)
    print("MARKETING EMAIL DETECTOR - GROUPED TEST + AUTO CLASSIFY")
    print("=" * 70)
    print()

    # Inicializovat DB
    print("🔧 Inicializuji databázi...")
    init_db()
    print("✓ Databáze připravena")
    print()

    # Načíst emaily
    print("📧 Načítám emaily...")
    emails = load_emails(5000)
    print(f"✓ Načteno {len(emails)} emailů")
    print()

    # Seskupit
    print("📦 Seskupuji podobné emaily...")
    groups = group_emails(emails)
    print(f"✓ Vytvořeno {len(groups)} skupin")
    print()

    # Smart matching podle sendera (použít existující klasifikace)
    print("🔍 Smart matching podle senderu...")
    sender_map = load_sender_classifications()
    sender_matches = apply_sender_classification(groups, sender_map)
    print(f"✓ Aplikováno {sender_matches} klasifikací z DB (podle senderu)")
    print()

    # Načíst aktuální klasifikace před auto-klasifikací
    current_classifications = load_classifications()

    # Automaticky klasifikovat TOP skupiny (jen ty, co ještě nejsou klasifikované)
    print("🤖 Auto-klasifikace TOP skupin...")
    auto_count = auto_classify_top_groups(groups, current_classifications)
    print(f"✓ Automaticky klasifikováno {auto_count} NOVÝCH skupin (mobile.de, autoscout24, immowelt)")
    print()

    # Analyzovat
    print("🔍 Analyzuji skupiny pomocí AI...")
    groups = analyze_groups(groups)

    # Načíst VŠECHNY klasifikace z DB
    db_classifications = load_classifications()
    print(f"💾 Celkem klasifikací v DB: {len(db_classifications)}")
    print(f"   - Sender matches: {sender_matches}")
    print(f"   - Auto (blacklist): {auto_count}")
    print(f"   - Neklasifikováno: {len(groups) - len(db_classifications)}")
    print()

    # Statistiky
    total_emails = sum(g['count'] for g in groups)
    marketing_groups = sum(1 for g in groups if g['is_marketing'])
    marketing_emails = sum(g['count'] for g in groups if g['is_marketing'])
    avg_confidence = sum(g['confidence'] for g in groups) / len(groups) if groups else 0

    stats = {
        'total': total_emails,
        'marketing': marketing_emails,
        'marketing_pct': (marketing_emails / total_emails * 100) if total_emails else 0,
        'avg_confidence': avg_confidence,
        'groups': len(groups),
        'marketing_groups': marketing_groups
    }

    print("📊 STATISTIKY:")
    print(f"  Celkem emailů: {total_emails}")
    print(f"  Skupin: {len(groups)}")
    print(f"  Marketing skupin: {marketing_groups} ({marketing_groups/len(groups)*100:.1f}%)")
    print(f"  Marketing emailů: {marketing_emails} ({stats['marketing_pct']:.1f}%)")
    print(f"  Průměrná spolehlivost: {avg_confidence:.1f}%")
    print()

    # Top 10 nejčastějších skupin
    print("📈 TOP 10 nejčastějších skupin:")
    for i, group in enumerate(groups[:10], 1):
        auto_mark = " [AUTO ✓]" if group['id'] in db_classifications else ""
        print(f"  {i}. {group['count']:3d}× {group['from'][:30]:30s} - {group['subject_example'][:40]}{auto_mark}")
    print()

    # Generovat HTML
    print("🎨 Generuji HTML rozhraní...")
    html = generate_html(groups, stats, db_classifications)

    output_file = '/Users/m.a.j.puzik/apps/maj-subscriptions-local/marketing_test_results_grouped.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"✅ HTML vygenerováno: {output_file}")
    print()
    print(f"🌐 Otevři: file://{output_file}")
    print()
    print("✅ Hotovo!")
    print()
    print("ℹ️  Default zobrazení: jen NEKLASIFIKOVANÉ skupiny")
    print("   Tlačítko 'All' zobrazí všechny")
    print("   Tlačítko 'Classified' zobrazí jen klasifikované")

if __name__ == '__main__':
    main()
