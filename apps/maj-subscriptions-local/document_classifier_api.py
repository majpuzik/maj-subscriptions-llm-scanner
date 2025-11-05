#!/usr/bin/env python3
"""
Document Classification API для MAJ Subscriptions
Интеграция со стандартизированными модулями v2.0/v2.2
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from flask import jsonify, request

# Import standardizovaných modulů
try:
    from marketing_email_detector import MarketingEmailDetector
    MARKETING_AVAILABLE = True
except ImportError:
    MARKETING_AVAILABLE = False
    print("⚠ marketing_email_detector недоступен")

try:
    from legal_doc_identifier import LegalDocumentIdentifier
    LEGAL_AVAILABLE = True
except ImportError:
    LEGAL_AVAILABLE = False
    print("⚠ legal_doc_identifier недоступен")

try:
    from cz_receipt_intelligence import CzReceiptIntelligence
    RECEIPT_AVAILABLE = True
except ImportError:
    RECEIPT_AVAILABLE = False
    print("⚠ cz_receipt_intelligence недоступен")

try:
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    # Bank processor má nestandartní název s tečkou
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "bank_statement_processor",
        os.path.join(os.path.dirname(__file__), "bank_statement_processor_v2.2.py")
    )
    if spec and spec.loader:
        bank_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(bank_module)
        BankStatementProcessor = bank_module.BankStatementProcessor
        BANK_AVAILABLE = True
    else:
        BANK_AVAILABLE = False
except Exception as e:
    BANK_AVAILABLE = False
    print(f"⚠ bank_statement_processor недоступен: {e}")


class UniversalDocumentClassifier:
    """
    Универсальный классификатор документов
    Использует все доступные стандартизированные модули
    """

    def __init__(self):
        self.marketing_detector = MarketingEmailDetector() if MARKETING_AVAILABLE else None
        self.legal_identifier = LegalDocumentIdentifier() if LEGAL_AVAILABLE else None
        self.receipt_analyzer = CzReceiptIntelligence() if RECEIPT_AVAILABLE else None
        self.bank_processor = BankStatementProcessor() if BANK_AVAILABLE else None

    def classify_document(self, file_path: str, text_content: Optional[str] = None) -> Dict[str, Any]:
        """
        Классифицирует документ используя все доступные модули

        Args:
            file_path: Путь к файлу
            text_content: Текстовое содержимое (опционально)

        Returns:
            Результат классификации в стандартизированном формате
        """
        results = []

        # Получить текстовое содержимое
        if text_content is None:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    text_content = f.read()
            except Exception as e:
                return {
                    'error': f'Не удалось прочитать файл: {str(e)}',
                    'file_path': file_path
                }

        # 0. Marketing Email Detector (HIGHEST PRIORITY - runs FIRST!)
        if self.marketing_detector and text_content:
            try:
                # Extract email metadata from text/filename
                subject = Path(file_path).stem if file_path else ''
                from_addr = ''

                # Try to extract subject and from from text if it looks like email
                lines = text_content.split('\n')[:10]  # First 10 lines
                for line in lines:
                    if line.startswith('Subject:'):
                        subject = line.replace('Subject:', '').strip()
                    elif line.startswith('From:'):
                        from_addr = line.replace('From:', '').strip()

                email_data = {
                    'subject': subject,
                    'from': from_addr,
                    'body': text_content[:5000],  # First 5000 chars
                    'html_body': ''
                }

                is_marketing, confidence, details = self.marketing_detector.analyze(email_data)

                # DEBUG: Log what we're analyzing
                print(f"DEBUG: Marketing detector - Subject: '{email_data['subject'][:80]}'")
                print(f"DEBUG: Marketing detector - Confidence: {confidence}%, is_marketing: {is_marketing}")
                print(f"DEBUG: Marketing detector - Reasons: {details.get('reasons', [])}")

                # If marketing detected with high confidence, SKIP other modules!
                # Threshold lowered to 25 for German marketing emails (2 keywords = 25-30 points)
                if is_marketing and confidence >= 25:
                    return {
                        'document_type': 'marketing_email',
                        'confidence': confidence,
                        'country': 'UNKNOWN',
                        'version': '1.4',
                        'paperless': {
                            'tags': ['marketing', 'email', 'newsletter'],
                            'custom_fields': {},
                            'document_type_name': 'Marketing Email'
                        },
                        'metadata': {
                            'classified_by': 'marketing_email_detector',
                            'is_marketing': True,
                            'marketing_details': details,
                            'file_path': file_path
                        }
                    }
            except Exception as e:
                print(f"⚠ Marketing detector error: {e}")

        # 1. Legal Document Identifier
        if self.legal_identifier and text_content:
            try:
                legal_result = self.legal_identifier.analyze_document(text_content)
                if legal_result['confidence'] > 70:  # Increased threshold to prevent false positives
                    results.append({
                        'module': 'legal_doc_identifier',
                        'module_version': legal_result['version'],
                        'result': legal_result
                    })
            except Exception as e:
                print(f"⚠ Legal identifier error: {e}")

        # 2. CZ Receipt Intelligence
        if self.receipt_analyzer:
            try:
                receipt_result = self.receipt_analyzer.analyze_document(file_path)
                if receipt_result['confidence'] > 20:  # Nižší порог для receipts
                    results.append({
                        'module': 'cz_receipt_intelligence',
                        'module_version': receipt_result['version'],
                        'result': receipt_result
                    })
            except Exception as e:
                print(f"⚠ Receipt analyzer error: {e}")

        # 3. Bank Statement Processor
        if self.bank_processor and file_path.endswith('.xml'):
            try:
                bank_result = self.bank_processor.analyze_statement(file_path)
                if bank_result['confidence'] > 70:  # Increased threshold to prevent false positives
                    results.append({
                        'module': 'bank_statement_processor',
                        'module_version': bank_result['version'],
                        'result': bank_result
                    })
            except Exception as e:
                print(f"⚠ Bank processor error: {e}")

        # Если ничего не найдено
        if not results:
            return {
                'document_type': 'unknown',
                'confidence': 0,
                'country': 'UNKNOWN',
                'paperless': {
                    'tags': ['nerozpoznáno'],
                    'custom_fields': {},
                    'document_type_name': 'Nerozpoznaný dokument'
                },
                'metadata': {
                    'file_path': file_path,
                    'modules_tried': {
                        'legal': LEGAL_AVAILABLE,
                        'receipt': RECEIPT_AVAILABLE,
                        'bank': BANK_AVAILABLE
                    }
                }
            }

        # Vrátit nejlepší výsledek (s nejvyšší confidence)
        best_result = max(results, key=lambda x: x['result']['confidence'])

        # NULL filtering for correspondent/correspondent_name fields
        result = best_result['result'].copy()

        # Filter correspondent field
        if 'correspondent' in result:
            if result['correspondent'] in (None, 'null', 'NULL', '', 'None'):
                result['correspondent'] = None

        # Filter correspondent_name field (some modules use this)
        if 'correspondent_name' in result:
            if result['correspondent_name'] in (None, 'null', 'NULL', '', 'None'):
                result['correspondent_name'] = None

        # Filter paperless.correspondent if it exists
        if 'paperless' in result and 'correspondent' in result['paperless']:
            if result['paperless']['correspondent'] in (None, 'null', 'NULL', '', 'None'):
                result['paperless']['correspondent'] = None

        return {
            **result,
            'metadata': {
                **result.get('metadata', {}),
                'classified_by': best_result['module'],
                'all_results': results  # Все результаты для отладки
            }
        }

    def get_all_tags(self) -> List[str]:
        """
        Возвращает список всех возможных тегов из всех модулей
        """
        tags = set()

        # Legal tags
        tags.update([
            'soudní-spis', 'právní', 'předvolání', 'rozsudek', 'usnesení',
            'obvodní-soud', 'krajský-soud', 'vrchní-soud',
            'policejní-protokol', 'KRPA', 'administrativní',
            'státní-zastupitelství', 'cz', 'de'
        ])

        # Receipt tags
        tags.update([
            'účtenka', 'pohonné-hmoty', 'parking', 'restaurace',
            'potraviny', 'lékárna', 'mytí-aut', 'zasklení',
            'shell', 'omv', 'benzina', 'lidl', 'kaufland', 'albert',
            'eet', 'cz'
        ])

        # Bank tags
        tags.update([
            'bankovní-výpis', 'xml', 'finsta', 'camt-053',
            'banka-čsob', 'banka-moneta', 'banka-kb', 'cz'
        ])

        return sorted(list(tags))


def register_document_routes(app):
    """
    Регистрирует маршруты для классификации документов в Flask app
    """
    classifier = UniversalDocumentClassifier()

    @app.route('/api/documents/classify', methods=['POST'])
    def classify_document():
        """
        POST /api/documents/classify

        Body:
        - file: uploaded file (multipart/form-data)
        OR
        - text: text content (application/json)
        - filename: optional filename
        """
        try:
            # File upload
            if 'file' in request.files:
                file = request.files['file']
                if file.filename == '':
                    return jsonify({'error': 'Нет выбранного файла'}), 400

                # Сохранить временный файл
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp:
                    file.save(tmp.name)
                    result = classifier.classify_document(tmp.name)
                    os.unlink(tmp.name)
                    return jsonify(result)

            # Text content
            elif request.is_json:
                data = request.get_json()
                text = data.get('text', '')
                filename = data.get('filename', 'document.txt')

                if not text:
                    return jsonify({'error': 'Нет текстового содержимого'}), 400

                # Создать временный файл
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp:
                    tmp.write(text)
                    tmp.flush()
                    result = classifier.classify_document(tmp.name, text_content=text)
                    os.unlink(tmp.name)

                    result['metadata']['original_filename'] = filename
                    return jsonify(result)

            else:
                return jsonify({'error': 'Неподдерживаемый тип контента'}), 400

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/documents/tags')
    def get_all_tags():
        """
        GET /api/documents/tags

        Возвращает список всех возможных тегов Paperless
        """
        return jsonify({
            'tags': classifier.get_all_tags(),
            'count': len(classifier.get_all_tags())
        })

    @app.route('/api/documents/modules')
    def get_available_modules():
        """
        GET /api/documents/modules

        Возвращает информацию о доступных модулях
        """
        return jsonify({
            'modules': {
                'legal_doc_identifier': {
                    'available': LEGAL_AVAILABLE,
                    'version': '2.0' if LEGAL_AVAILABLE else None,
                    'types': ['court_document', 'police_document', 'prosecutor_document']
                },
                'cz_receipt_intelligence': {
                    'available': RECEIPT_AVAILABLE,
                    'version': '2.0.0' if RECEIPT_AVAILABLE else None,
                    'types': ['receipt']
                },
                'bank_statement_processor': {
                    'available': BANK_AVAILABLE,
                    'version': '2.2' if BANK_AVAILABLE else None,
                    'types': ['bank_statement']
                }
            }
        })

    print("✓ Document classification routes registered")
    return classifier
