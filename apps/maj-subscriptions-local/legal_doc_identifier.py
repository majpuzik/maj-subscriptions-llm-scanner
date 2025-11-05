#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Legal Document Identifier (Police + Court + Prosecutor, CZ/DE) v2.0
--------------------------------------------------------------------
Rozpoznává české a německé policejní, soudní a prokurátorské dokumenty.
Generuje tagy a custom fields pro Paperless-NGX.

CLI použití:
    python legal_doc_identifier.py /cesta/dokument.txt

Veřejné funkce:
    - analyze_document(text: str) -> dict (s Paperless integrací)
    - classify_document(text: str) -> (document_type, confidence, features)

Version History:
- v1.0: Základní rozpoznávání CZ/DE právních dokumentů
- v2.0: Přidána Paperless-NGX integrace (tagy, custom fields)

Autor: Claude Code + MCP Server
Datum: 2025-11-02
"""
import re
import json
from typing import Dict, Tuple, List
from enum import Enum

__version__ = "2.0"

class DocumentType(Enum):
    POLICE_LEGAL = "police_legal"
    POLICE_ADMIN = "police_admin"
    POLICE_ISDS = "police_isds"
    COURT_DOCUMENT = "court_document"
    PROSECUTOR_DOCUMENT = "prosecutor_doc"
    GERMAN_POLICE = "german_police"
    GERMAN_COURT = "german_court"
    NOT_LEGAL = "not_legal"
    UNKNOWN = "unknown"

class LegalDocumentIdentifier:
    def __init__(self):
        self.patterns = {
            'czech_police_headers': [r'POLICIE\s+ČESKÉ\s+REPUBLIKY', r'Krajské\s+ředitelství\s+policie'],
            'court_headers': [r'OBVODNÍ\s+SOUD', r'KRAJSKÝ\s+SOUD', r'VRCHNÍ\s+SOUD', r'MĚSTSKÝ\s+SOUD', r'ÚSTAVNÍ\s+SOUD'],
            'prosecutor_headers': [r'STÁTNÍ\s+ZASTUPITELSTVÍ', r'MĚSTSKÉ\s+STÁTNÍ', r'KRAJSKÉ\s+STÁTNÍ'],
            'legal_refs': [r'§\s*\d+\s*odstavec?\s*\d+', r'trestního\s+řádu'],
            'case_numbers': [r'\d+[A-Z]+\s*\d+/\d{4}', r'\d+\s+[A-Z]+\s+\d+/\d{4}', r'KRPA-\d+-\d+/[A-Z]+-\d+-\d+'],
            'court_types': [r'PŘEDVOLÁNÍ', r'ROZSUDEK', r'USNESENÍ', r'ODVOLÁNÍ'],
            'prosecutor_types': [r'KZV', r'TZ', r'vyrozumění', r'návrh\s+na\s+zastavení'],
            'signatures': [r'JUDr\.', r'samosoudce', r'státní\s+zástupce'],
            'german_court': [r'Amtsgericht', r'Landgericht', r'Oberlandesgericht'],
            'german_police': [r'Polizei', r'Bundespolizei'],
        }

    def extract_features(self, text: str) -> Dict:
        features = {}
        for key, pats in self.patterns.items():
            features[key] = any(re.search(p, text, re.IGNORECASE) for p in pats)
        return features

    def classify_document(self, text: str) -> Tuple[str, float, Dict]:
        f = self.extract_features(text)
        confidence = 0.0
        doc_type = DocumentType.NOT_LEGAL

        # Count supporting evidence (case numbers, legal refs, signatures)
        supporting_evidence = sum([
            f.get('case_numbers', False),
            f.get('legal_refs', False),
            f.get('signatures', False)
        ])

        # German documents - require multiple indicators for high confidence
        if f['german_court']:
            if supporting_evidence >= 1:
                return DocumentType.GERMAN_COURT, 0.9, f  # Has supporting evidence
            else:
                return DocumentType.GERMAN_COURT, 0.5, f  # Only keyword - LOW confidence

        if f['german_police']:
            if supporting_evidence >= 1:
                return DocumentType.GERMAN_POLICE, 0.9, f  # Has supporting evidence
            else:
                return DocumentType.GERMAN_POLICE, 0.5, f  # Only keyword - LOW confidence

        # Czech court documents - require multiple indicators
        if f['court_headers']:
            if supporting_evidence >= 1 or f.get('court_types', False):
                return DocumentType.COURT_DOCUMENT, 0.9, f
            else:
                return DocumentType.COURT_DOCUMENT, 0.6, f  # Only header - MEDIUM confidence

        # Prosecutor documents - require multiple indicators
        if f['prosecutor_headers']:
            if supporting_evidence >= 1 or f.get('prosecutor_types', False):
                return DocumentType.PROSECUTOR_DOCUMENT, 0.9, f
            else:
                return DocumentType.PROSECUTOR_DOCUMENT, 0.6, f  # Only header - MEDIUM confidence

        # Czech police - already has good logic
        if f['czech_police_headers'] and (f['legal_refs'] or f['case_numbers']):
            return DocumentType.POLICE_LEGAL, 0.9, f
        if f['czech_police_headers']:
            return DocumentType.POLICE_ADMIN, 0.7, f

        if any(f.values()):
            return DocumentType.UNKNOWN, 0.5, f
        return DocumentType.NOT_LEGAL, confidence, f

    def _extract_metadata(self, text: str, doc_type: DocumentType) -> Dict:
        """Extrahuje metadata z právního dokumentu"""
        metadata = {}

        # Číslo spisu
        case_patterns = [
            r'(?:sp\.\s*zn\.|spisová\s+značka|Sp\.\s*zn\.)\s*:?\s*(\d+\s*[A-Z]+\s*\d+/\d{4})',
            r'(KRPA-\d+-\d+/[A-Z]+-\d+-\d+)',
            r'(\d+\s+[A-Z]+\s+\d+/\d{4})'
        ]
        for pattern in case_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                metadata['case_number'] = match.group(1).strip()
                break

        # Název soudu/instituce
        if doc_type == DocumentType.COURT_DOCUMENT:
            court_match = re.search(r'((?:OBVODNÍ|KRAJSKÝ|VRCHNÍ|MĚSTSKÝ|ÚSTAVNÍ)\s+SOUD[^\n]*)', text, re.IGNORECASE)
            if court_match:
                metadata['court_name'] = court_match.group(1).strip()

        elif doc_type in (DocumentType.GERMAN_COURT,):
            court_match = re.search(r'((?:Amtsgericht|Landgericht|Oberlandesgericht)[^\n]*)', text, re.IGNORECASE)
            if court_match:
                metadata['court_name'] = court_match.group(1).strip()

        elif doc_type == DocumentType.PROSECUTOR_DOCUMENT:
            proc_match = re.search(r'((?:STÁTNÍ|MĚSTSKÉ|KRAJSKÉ)\s+ZASTUPITELSTVÍ[^\n]*)', text, re.IGNORECASE)
            if proc_match:
                metadata['prosecutor_name'] = proc_match.group(1).strip()

        elif doc_type in (DocumentType.POLICE_LEGAL, DocumentType.POLICE_ADMIN):
            police_match = re.search(r'(Krajské\s+ředitelství\s+policie[^\n]*)', text, re.IGNORECASE)
            if police_match:
                metadata['police_department'] = police_match.group(1).strip()

        # Typ dokumentu (předvolání, rozsudek, atd.)
        doc_subtypes = {
            'PŘEDVOLÁNÍ': 'Předvolání',
            'ROZSUDEK': 'Rozsudek',
            'USNESENÍ': 'Usnesení',
            'ODVOLÁNÍ': 'Odvolání',
            'KZV': 'Konečné zastavení věci',
            'TZ': 'Trestní zákon'
        }
        for keyword, subtype in doc_subtypes.items():
            if re.search(keyword, text, re.IGNORECASE):
                metadata['document_subtype'] = subtype
                break

        return metadata

    def _get_paperless_tags(self, doc_type: DocumentType, country: str, metadata: Dict) -> List[str]:
        """Generuje tagy pro Paperless-NGX"""
        tags = []

        # Základní typ dokumentu
        if doc_type == DocumentType.POLICE_LEGAL:
            tags.extend(['policejní-protokol', 'právní', 'KRPA'])
        elif doc_type == DocumentType.POLICE_ADMIN:
            tags.extend(['policejní-protokol', 'administrativní'])
        elif doc_type == DocumentType.COURT_DOCUMENT:
            tags.extend(['soudní-spis', 'právní'])
            # Typ soudního dokumentu
            if metadata.get('document_subtype'):
                tags.append(metadata['document_subtype'].lower())
            # Typ soudu
            if metadata.get('court_name'):
                if 'OBVODNÍ' in metadata['court_name'].upper():
                    tags.append('obvodní-soud')
                elif 'KRAJSKÝ' in metadata['court_name'].upper():
                    tags.append('krajský-soud')
                elif 'VRCHNÍ' in metadata['court_name'].upper():
                    tags.append('vrchní-soud')
        elif doc_type == DocumentType.PROSECUTOR_DOCUMENT:
            tags.extend(['státní-zastupitelství', 'právní'])
            if metadata.get('document_subtype'):
                tags.append(metadata['document_subtype'].lower().replace(' ', '-'))
        elif doc_type == DocumentType.GERMAN_POLICE:
            tags.extend(['policejní-protokol', 'právní'])
        elif doc_type == DocumentType.GERMAN_COURT:
            tags.extend(['soudní-spis', 'právní'])

        # Země
        tags.append(country.lower())

        return tags

    def _get_paperless_custom_fields(self, doc_type: DocumentType, metadata: Dict) -> Dict:
        """Generuje custom fields pro Paperless-NGX"""
        fields = {}

        if metadata.get('case_number'):
            fields['case_number'] = metadata['case_number']

        if metadata.get('court_name'):
            fields['court_name'] = metadata['court_name']

        if metadata.get('prosecutor_name'):
            fields['prosecutor_name'] = metadata['prosecutor_name']

        if metadata.get('police_department'):
            fields['police_department'] = metadata['police_department']

        if metadata.get('document_subtype'):
            fields['document_subtype'] = metadata['document_subtype']

        return fields

    def analyze_document(self, text: str) -> Dict:
        """
        Analyzuje právní dokument a vrací strukturovaný výstup pro Paperless-NGX

        Args:
            text: Text dokumentu

        Returns:
            Dict podle PAPERLESS_INTEGRATION_STANDARD
        """
        doc_type, conf, f = self.classify_document(text)

        # Určení země
        if doc_type in (DocumentType.GERMAN_COURT, DocumentType.GERMAN_POLICE):
            country = 'DE'
        elif doc_type in (DocumentType.NOT_LEGAL, DocumentType.UNKNOWN):
            country = 'UNKNOWN'
        else:
            country = 'CZ'

        # Extrakce metadata
        metadata = self._extract_metadata(text, doc_type)

        # Generování tagů
        tags = self._get_paperless_tags(doc_type, country, metadata)

        # Generování custom fields
        custom_fields = self._get_paperless_custom_fields(doc_type, metadata)

        # Document type name mapping
        type_names = {
            DocumentType.POLICE_LEGAL: 'Policejní protokol - právní',
            DocumentType.POLICE_ADMIN: 'Policejní protokol - administrativní',
            DocumentType.COURT_DOCUMENT: 'Soudní dokument',
            DocumentType.PROSECUTOR_DOCUMENT: 'Prokurátorský dokument',
            DocumentType.GERMAN_POLICE: 'Německý policejní protokol',
            DocumentType.GERMAN_COURT: 'Německý soudní dokument',
            DocumentType.NOT_LEGAL: 'Neprávní dokument',
            DocumentType.UNKNOWN: 'Neznámý typ'
        }

        doc_type_name = type_names.get(doc_type, 'Neznámý dokument')
        if metadata.get('document_subtype'):
            doc_type_name += f' - {metadata["document_subtype"]}'

        # Correspondent (instituce)
        correspondent = None
        if metadata.get('court_name'):
            correspondent = metadata['court_name']
        elif metadata.get('prosecutor_name'):
            correspondent = metadata['prosecutor_name']
        elif metadata.get('police_department'):
            correspondent = metadata['police_department']

        # Standardizovaný výstup
        result = {
            'document_type': doc_type.value,
            'confidence': int(conf * 100),  # Convert 0.9 to 90
            'country': country,
            'version': __version__,

            'paperless': {
                'tags': tags,
                'custom_fields': custom_fields,
                'document_type_name': doc_type_name
            },

            'metadata': {
                'is_legal_document': doc_type not in (DocumentType.NOT_LEGAL, DocumentType.UNKNOWN),
                'features': f,
                'extracted_metadata': metadata
            }
        }

        # Optional fields
        if correspondent:
            result['paperless']['correspondent'] = correspondent

        return result

def main():
    import argparse, sys, json
    ap = argparse.ArgumentParser(description="Identify legal document type (CZ/DE police/court)")
    ap.add_argument("file", help="Cesta k souboru")
    args = ap.parse_args()
    path = args.file
    text = open(path, encoding='utf-8').read()
    identifier = LegalDocumentIdentifier()
    res = identifier.analyze_document(text)
    print(json.dumps(res, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
