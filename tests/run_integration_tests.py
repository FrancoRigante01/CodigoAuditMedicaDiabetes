"""
Integration tests for document processing pipeline.
Tests the complete workflow: document reading -> classification -> field extraction -> output formatting.
"""

import json
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.document_reader import DocumentReader
from src.classifier import DocumentClassifier
from src.field_extractor import FieldExtractor
from src.output_formatter import OutputFormatter
from src.error_handler import ProcessingLogger, ErrorHandler


class IntegrationTester:
    """Runs integration tests on the document processing pipeline."""
    
    def __init__(self):
        self.logger = ProcessingLogger(enable_debug=True, log_file=None)
        self.error_handler = ErrorHandler()
        self.results = []
        self.test_dir = Path(__file__).parent / "test_documents"
    
    def test_document(self, doc_path: Path, expected_type: str) -> dict:
        """
        Test a single document through the full pipeline.
        
        Returns:
            dict: Test result with status, output, and any errors
        """
        test_name = f"{expected_type}_{doc_path.stem}"
        result = {
            "test_name": test_name,
            "document": str(doc_path),
            "expected_type": expected_type,
            "status": "pending",
            "errors": [],
            "output": None,
            "classification": None,
            "fields_extracted": 0
        }
        
        try:
            # Step 1: Read document
            reader = DocumentReader(use_ocr=False)
            text, images, metadata = reader.read_document(doc_path)
            result["read_status"] = "success"
            result["metadata"] = metadata
            
            # Step 2: Classify document
            classifier = DocumentClassifier()
            doc_type, confidence = classifier.classify_document(text, images, metadata)
            result["classification"] = {
                "type": doc_type,
                "confidence": confidence
            }
            
            # Step 3: Extract fields
            extractor = FieldExtractor()
            fields = extractor.extract_fields(doc_type, text, images, metadata)
            result["fields_extracted"] = len([f for f in fields.values() if f.get("valor") != "NOT_FOUND"])
            
            # Step 4: Format output
            formatter = OutputFormatter()
            output = formatter.format_result(doc_type, confidence, fields, [])
            result["output"] = output.to_json_dict()
            result["status"] = "success"
            
            # Validation
            if doc_type != expected_type:
                result["warnings"] = [f"Classification mismatch: expected {expected_type}, got {doc_type}"]
            
        except Exception as e:
            result["status"] = "failed"
            result["errors"].append(str(e))
            self.error_handler.handle_error(
                error_type="extraction_failed",
                error_details={"reason": str(e)},
                raise_exception=False
            )
        
        return result
    
    def run_all_tests(self) -> None:
        """Run all integration tests."""
        print("\n" + "="*80)
        print("DOCUMENT PROCESSING PIPELINE - INTEGRATION TESTS")
        print("="*80 + "\n")
        
        # Test cases: (document_path, expected_type)
        test_cases = [
            (self.test_dir / "formulario_diabetes" / "formulario_diabetes_sample.png", "formulario_diabetes"),
            (self.test_dir / "laboratorio" / "laboratorio_sample.png", "laboratorio"),
            (self.test_dir / "prescripcion" / "prescripcion_sample.png", "prescripcion"),
            (self.test_dir / "estudio_diagnostico" / "estudio_diagnostico_sample.png", "estudio_diagnostico"),
            (self.test_dir / "formulario_diabetes" / "formulario_low_quality.png", "formulario_diabetes"),
        ]
        
        for doc_path, expected_type in test_cases:
            print(f"\nTesting: {doc_path.name}")
            print("-" * 60)
            
            if not doc_path.exists():
                print(f"✗ File not found: {doc_path}")
                continue
            
            result = self.test_document(doc_path, expected_type)
            self.results.append(result)
            
            # Print result
            status_symbol = "✓" if result["status"] == "success" else "✗"
            print(f"{status_symbol} Status: {result['status']}")
            
            if result.get("classification"):
                print(f"  Classification: {result['classification']['type']} (confidence: {result['classification']['confidence']}%)")
            
            if result.get("fields_extracted"):
                print(f"  Fields extracted: {result['fields_extracted']}")
            
            if result.get("warnings"):
                for warning in result["warnings"]:
                    print(f"  ⚠ {warning}")
            
            if result.get("errors"):
                for error in result["errors"]:
                    print(f"  ✗ Error: {error}")
        
        # Summary
        self._print_summary()
    
    def _print_summary(self) -> None:
        """Print test summary."""
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80 + "\n")
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r["status"] == "success")
        failed = total - passed
        
        print(f"Total tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success rate: {(passed/total*100):.1f}%\n")
        
        # Detailed results table
        print("Detailed Results:")
        print("-" * 80)
        print(f"{'Test Name':<40} {'Status':<10} {'Classification':<20}")
        print("-" * 80)
        
        for result in self.results:
            test_name = result["test_name"][:39]
            status = result["status"]
            classification = result["classification"]["type"] if result.get("classification") else "N/A"
            print(f"{test_name:<40} {status:<10} {classification:<20}")
        
        print("-" * 80)
        
        # Save results to JSON
        results_file = Path(__file__).parent / "test_results.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"\nResults saved to: {results_file}\n")
    
    def print_sample_output(self) -> None:
        """Print sample output JSON for one successful test."""
        print("\n" + "="*80)
        print("SAMPLE OUTPUT JSON")
        print("="*80 + "\n")
        
        for result in self.results:
            if result["status"] == "success" and result.get("output"):
                print(f"Sample: {result['test_name']}\n")
                print(json.dumps(result["output"], indent=2, ensure_ascii=False))
                break


def main():
    """Run integration tests."""
    tester = IntegrationTester()
    tester.run_all_tests()
    tester.print_sample_output()


if __name__ == "__main__":
    main()
