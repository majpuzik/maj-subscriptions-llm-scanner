#!/bin/bash
#
# Paperless-NGX Pre-Consume Script with Document Classification
# Calls document_classifier_wrapper.py directly via Docker exec
#

DOCUMENT_PATH="$1"
BASENAME=$(basename "$DOCUMENT_PATH")
DIRNAME=$(dirname "$DOCUMENT_PATH")

# Debug output
echo "[PRE-CONSUME] Processing: $BASENAME" >&2

# STEP 2: Extract text for classification
TEMP_TEXT="/tmp/paperless_classify_$$.txt"
FILE_TYPE=$(file -b --mime-type "$DOCUMENT_PATH" 2>/dev/null || echo "unknown")

# Extract text based on file type
case "$FILE_TYPE" in
    "application/pdf")
        # PDF - use pdftotext
        if command -v pdftotext >/dev/null 2>&1; then
            pdftotext "$DOCUMENT_PATH" "$TEMP_TEXT" 2>/dev/null || echo "" > "$TEMP_TEXT"
            echo "[PRE-CONSUME] Extracted text from PDF" >&2
        else
            echo "" > "$TEMP_TEXT"
        fi
        ;;
    image/*)
        # Image - use tesseract if available
        if command -v tesseract >/dev/null 2>&1; then
            tesseract "$DOCUMENT_PATH" "${TEMP_TEXT%%.txt}" -l ces+eng 2>/dev/null || echo "" > "$TEMP_TEXT"
            echo "[PRE-CONSUME] OCR from image" >&2
        else
            echo "" > "$TEMP_TEXT"
        fi
        ;;
    "text/plain"|"text/"*)
        # Text file
        cp "$DOCUMENT_PATH" "$TEMP_TEXT" 2>/dev/null || echo "" > "$TEMP_TEXT"
        ;;
    *)
        # Unknown - try as text
        cat "$DOCUMENT_PATH" 2>/dev/null | head -c 100000 > "$TEMP_TEXT" || echo "" > "$TEMP_TEXT"
        ;;
esac

# STEP 3: Classify document via unified-mcp-server
if [ -s "$TEMP_TEXT" ]; then
    echo "[PRE-CONSUME] Classifying document..." >&2

    # Copy temp text to unified-mcp-server container
    docker cp "$TEMP_TEXT" unified-mcp-server:/tmp/classify_temp.txt 2>/dev/null

    # Run classification in unified-mcp-server container
    CLASSIFICATION=$(docker exec unified-mcp-server python3 /app/document_classifier_wrapper.py --classify /tmp/classify_temp.txt --json 2>/dev/null)

    if [ $? -eq 0 ] && [ -n "$CLASSIFICATION" ]; then
        echo "[PRE-CONSUME] Classification result: $CLASSIFICATION" >&2

        # STEP 4: Create Paperless metadata JSON
        METADATA_FILE="${DOCUMENT_PATH}.json"

        # Parse JSON results (simple grep-based parsing)
        DOC_TYPE=$(echo "$CLASSIFICATION" | grep -o '"type"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/.*"\([^"]*\)".*/\1/')
        CORRESPONDENT=$(echo "$CLASSIFICATION" | grep -o '"correspondent"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/.*"\([^"]*\)".*/\1/')
        CONFIDENCE=$(echo "$CLASSIFICATION" | grep -o '"confidence"[[:space:]]*:[[:space:]]*[0-9]*' | grep -o '[0-9]*')

        # Map our document types to Paperless types
        case "$DOC_TYPE" in
            "invoice")
                PAPERLESS_TYPE="faktura"
                ;;
            "receipt")
                PAPERLESS_TYPE="účtenka"
                ;;
            "bank_statement")
                PAPERLESS_TYPE="bankovní výpis"
                ;;
            "police_protocol_cz"|"police_protocol_de")
                PAPERLESS_TYPE="policejní protokol"
                ;;
            "court_summons")
                PAPERLESS_TYPE="soudní předvolání"
                ;;
            "court_verdict")
                PAPERLESS_TYPE="soudní rozsudek"
                ;;
            "court_decision")
                PAPERLESS_TYPE="soudní usnesení"
                ;;
            "prosecutor_decision")
                PAPERLESS_TYPE="rozhodnutí státního zastupitelství"
                ;;
            *)
                PAPERLESS_TYPE=""
                ;;
        esac

        # Create metadata JSON for Paperless
        if [ -n "$PAPERLESS_TYPE" ] && [ "$CONFIDENCE" -ge 50 ]; then
            cat > "$METADATA_FILE" <<METAEOF
{
  "title": "$(echo $BASENAME | sed 's/\.[^.]*$//')$([ -n "$CORRESPONDENT" ] && echo " - $CORRESPONDENT" || echo "")",
  "document_type": "$PAPERLESS_TYPE",
  "correspondent": "$([ -n "$CORRESPONDENT" ] && echo "$CORRESPONDENT" || echo "neznámý")"
}
METAEOF
            echo "[PRE-CONSUME] Created metadata: $METADATA_FILE" >&2
            echo "[PRE-CONSUME] Type: $PAPERLESS_TYPE, Correspondent: $CORRESPONDENT, Confidence: $CONFIDENCE%" >&2
        else
            echo "[PRE-CONSUME] Confidence too low ($CONFIDENCE%) or no type detected, skipping metadata" >&2
        fi
    else
        echo "[PRE-CONSUME] Classification failed" >&2
    fi

    # Cleanup
    docker exec unified-mcp-server rm -f /tmp/classify_temp.txt 2>/dev/null
else
    echo "[PRE-CONSUME] No text extracted, skipping classification" >&2
fi

# Cleanup
rm -f "$TEMP_TEXT"

# Return document path
echo "$DOCUMENT_PATH"
