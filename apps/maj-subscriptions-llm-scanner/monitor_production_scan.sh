#!/bin/bash
# Monitoring script pro produkční LLM scan

echo "================================================================================"
echo "📊 PRODUKČNÍ LLM SCAN - MONITORING"
echo "================================================================================"
echo ""

# Zkontrolovat, zda proces běží
if [ -f /tmp/production_scan.pid ]; then
    PID=$(cat /tmp/production_scan.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "✅ Scan BĚŽÍ (PID: $PID)"
        echo ""
    else
        echo "❌ Scan NENÍ SPUŠTĚNÝ (PID $PID neexistuje)"
        echo ""
    fi
else
    echo "⚠️  PID soubor nenalezen"
    echo ""
fi

# Statistiky z databáze
if [ -f /tmp/production_subscriptions.db ]; then
    echo "📈 DATABÁZOVÉ STATISTIKY:"
    echo "----------------------------------------"

    # Počet nalezených předplatných
    TOTAL_SUBS=$(sqlite3 /tmp/production_subscriptions.db "SELECT COUNT(*) FROM email_evidence" 2>/dev/null || echo "0")
    echo "  Nalezená předplatná: $TOTAL_SUBS"

    # Počet služeb
    TOTAL_SERVICES=$(sqlite3 /tmp/production_subscriptions.db "SELECT COUNT(*) FROM services WHERE detected_via='llm_scanner'" 2>/dev/null || echo "0")
    echo "  Nové služby: $TOTAL_SERVICES"

    # Průměrná confidence
    AVG_CONF=$(sqlite3 /tmp/production_subscriptions.db "SELECT ROUND(AVG(confidence_score), 1) FROM email_evidence" 2>/dev/null || echo "0")
    echo "  Průměrná confidence: ${AVG_CONF}%"

    echo ""

    # Top 10 služeb
    if [ "$TOTAL_SUBS" -gt "0" ]; then
        echo "🏆 TOP 10 SLUŽEB:"
        echo "----------------------------------------"
        sqlite3 /tmp/production_subscriptions.db "
            SELECT s.name, COUNT(e.id) as count
            FROM services s
            LEFT JOIN email_evidence e ON s.id = e.service_id
            WHERE s.detected_via = 'llm_scanner'
            GROUP BY s.id
            ORDER BY count DESC
            LIMIT 10
        " 2>/dev/null | awk '{printf "  %2d. %s\n", NR, $0}'
        echo ""
    fi
fi

# Poslední řádky z logu
echo "📋 POSLEDNÍ AKTIVITA (tail -20):"
echo "----------------------------------------"
if [ -f /tmp/production_scan_20251031_213126.log ]; then
    tail -20 /tmp/production_scan_20251031_213126.log | grep -E "INFO|ERROR|WARNING" | sed 's/^/  /'
elif [ -f /tmp/production_scan_console.log ]; then
    tail -20 /tmp/production_scan_console.log | grep -E "INFO|ERROR|WARNING" | sed 's/^/  /'
else
    echo "  (log soubor nenalezen)"
fi

echo ""
echo "================================================================================"
echo "💡 PŘÍKAZY:"
echo "  - Sledovat v reálném čase: tail -f /tmp/production_scan_20251031_213126.log"
echo "  - Aktuální progress: sqlite3 /tmp/production_subscriptions.db 'SELECT COUNT(*) FROM email_evidence'"
echo "  - Zastavit scan: kill \$(cat /tmp/production_scan.pid)"
echo "================================================================================"
