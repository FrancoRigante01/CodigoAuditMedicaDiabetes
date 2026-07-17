#!/usr/bin/env python
"""
Demo script showing how to use the Document Classification module.

This script processes sample documents and displays formatted results.
⚠️ IMPORTANT: This is a DEMO with fictional data. Do NOT use with real patient data
without implementing proper security, encryption, and compliance measures.
"""

import json
from pathlib import Path
from typing import Dict, List

# Mock classes to demonstrate the pipeline without requiring all dependencies
class MockDocumentReader:
    """Mock reader that simulates document reading."""
    
    def read_document(self, path: Path):
        """Simulate reading a document."""
        return "Sample text content", [], {"format": "png", "page_count": 1}

class MockClassifier:
    """Mock classifier that returns expected types."""
    
    TYPE_MAPPING = {
        "formulario_diabetes": ("formulario_diabetes", 92),
        "laboratorio": ("laboratorio", 88),
        "prescripcion": ("prescripcion", 95),
        "estudio_diagnostico": ("estudio_diagnostico", 90),
        "low_quality": ("formulario_diabetes", 65)
    }
    
    def classify_document(self, text, images, metadata):
        """Simulate document classification."""
        # Determine type from filename
        for key, (doc_type, conf) in self.TYPE_MAPPING.items():
            if key in text.lower():
                return doc_type, conf
        return "estudio_diagnostico", 75

class MockFieldExtractor:
    """Mock field extractor that returns expected fields."""
    
    FIELD_TEMPLATES = {
        "formulario_diabetes": {
            "diagnostico": ("Diabetes Mellitus tipo 2", 95),
            "tipo_diabetes": ("tipo 2", 90),
            "medicacion_solicitada": ("Metformina 500mg, Enalapril 10mg", 88),
            "insumo_solicitado": ("Tiras reactivas, lancetas", 85),
            "fecha_firma": ("12/07/2024", 98),
            "datos_medico": ("Dr. Roberto Martínez López, MP-2024-001567", 92)
        },
        "laboratorio": {
            "tipo_estudio": ("Glucemia en Ayunas, HbA1c", 92),
            "fecha_estudio": ("08/07/2024", 96),
            "valores_relevantes": ("Glucemia: 145 mg/dL, HbA1c: 7.8%", 90)
        },
        "prescripcion": {
            "medicacion_insumo": ("Metformina 850mg, Bromocriptina 2.5mg", 94),
            "dosis": ("1 comprimido c/12hs, 1/2 comprimido en la mañana", 89),
            "vigencia_receta": ("30 días, válida hasta 13/08/2024", 97),
            "matricula_prescriptor": ("MP-1985-002456", 93)
        },
        "estudio_diagnostico": {
            "tipo_informe": ("Ecocardiografía", 91),
            "fecha": ("11/07/2024", 99),
            "conclusion_relevante": ("Función sistólica y diastólica conservadas. Sin hallazgos patológicos", 87)
        }
    }
    
    def extract_fields(self, doc_type, text, images, metadata):
        """Simulate field extraction."""
        template = self.FIELD_TEMPLATES.get(doc_type, {})
        return {
            field_name: {"valor": valor, "confianza": confianza}
            for field_name, (valor, confianza) in template.items()
        }

class MockOutputFormatter:
    """Mock formatter that returns expected JSON structure."""
    
    def format_result(self, doc_type: str, confidence: int, fields: Dict, issues: List) -> 'MockResult':
        """Format results into expected structure."""
        return MockResult(doc_type, confidence, fields, issues)

class MockResult:
    """Mock result object."""
    
    def __init__(self, doc_type: str, confidence: int, fields: Dict, issues: List):
        self.doc_type = doc_type
        self.confidence = confidence
        self.fields = fields
        self.issues = issues
    
    def to_json_dict(self):
        return {
            "tipo_documento": self.doc_type,
            "confianza_clasificacion": self.confidence,
            "campos_extraidos": self.fields,
            "faltantes_o_inconsistencias": self.issues
        }

def process_document(doc_path: Path) -> Dict:
    """
    Process a single document through the complete pipeline.
    
    Args:
        doc_path: Path to the document
        
    Returns:
        Dictionary with processing results
    """
    reader = MockDocumentReader()
    classifier = MockClassifier()
    extractor = MockFieldExtractor()
    formatter = MockOutputFormatter()
    
    # Step 1: Read
    text, images, metadata = reader.read_document(doc_path)
    
    # Step 2: Classify
    doc_type, confidence = classifier.classify_document(text, images, metadata)
    
    # Step 3: Extract fields
    fields = extractor.extract_fields(doc_type, text, images, metadata)
    
    # Step 4: Format
    result = formatter.format_result(doc_type, confidence, fields, [])
    
    return result.to_json_dict()

def print_header(title: str):
    """Print formatted header."""
    print("\n" + "=" * 80)
    print(title.center(80))
    print("=" * 80 + "\n")

def print_result(doc_type: str, result: Dict):
    """Print a single result in formatted way."""
    print(f"\n📄 Tipo de Documento: {result['tipo_documento']}")
    print(f"📊 Confianza Clasificación: {result['confianza_clasificacion']}%")
    print(f"🔍 Campos Extraídos: {len(result['campos_extraidos'])}")
    
    # Show confidence distribution
    confidences = [f['confianza'] for f in result['campos_extraidos'].values()]
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0
    print(f"📈 Confianza Promedio Campos: {avg_confidence:.1f}%")
    
    if result['faltantes_o_inconsistencias']:
        print(f"⚠️ Problemas Detectados: {len(result['faltantes_o_inconsistencias'])}")
        for issue in result['faltantes_o_inconsistencias']:
            print(f"   - {issue}")
    else:
        print("✓ Sin inconsistencias detectadas")

def main():
    """Run the demo."""
    
    print_header("DEMO: Módulo de Ingesta y Clasificación Documental")
    
    print("⚠️ AVISO: Este es un módulo DEMO con datos ficticios.")
    print("NO debe usarse con datos reales de pacientes sin auditoría de seguridad.")
    print()
    
    # Define test documents
    test_documents = [
        {
            "path": "tests/test_documents/formulario_diabetes/formulario_diabetes_sample.png",
            "name": "Formulario de Diabetes - Muestra",
            "type": "formulario_diabetes"
        },
        {
            "path": "tests/test_documents/laboratorio/laboratorio_sample.png",
            "name": "Estudios de Laboratorio",
            "type": "laboratorio"
        },
        {
            "path": "tests/test_documents/prescripcion/prescripcion_sample.png",
            "name": "Prescripción Médica",
            "type": "prescripcion"
        },
        {
            "path": "tests/test_documents/estudio_diagnostico/estudio_diagnostico_sample.png",
            "name": "Informe Diagnóstico",
            "type": "estudio_diagnostico"
        }
    ]
    
    # Process documents
    results = []
    print("Procesando documentos de prueba...\n")
    print("-" * 80)
    
    for idx, doc_info in enumerate(test_documents, 1):
        print(f"\n[{idx}/{len(test_documents)}] {doc_info['name']}")
        
        try:
            result = process_document(Path(doc_info['path']))
            results.append(result)
            print_result(doc_info['type'], result)
            print("✓ Procesado exitosamente")
        except Exception as e:
            print(f"✗ Error al procesar: {e}")
    
    # Summary
    print_header("RESUMEN DE PROCESAMIENTO")
    
    print(f"Total documentos procesados: {len(results)}")
    print(f"Documentos exitosos: {len(results)}")
    
    if results:
        avg_classification_confidence = sum(r['confianza_clasificacion'] for r in results) / len(results)
        print(f"Confianza promedio clasificación: {avg_classification_confidence:.1f}%")
        
        total_fields = sum(len(r['campos_extraidos']) for r in results)
        print(f"Campos extraídos totales: {total_fields}")
    
    # Show sample output
    print_header("EJEMPLO DE OUTPUT JSON")
    
    if results:
        print("Resultado del primer documento procesado:\n")
        print(json.dumps(results[0], indent=2, ensure_ascii=False))
    
    # Save results
    output_file = Path("demo_results.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print_header("FINALIZADO")
    print(f"✓ Resultados guardados en: {output_file}")
    print("\nPróximos pasos:")
    print("1. Revisa la USAGE_GUIDE.md para más ejemplos de uso")
    print("2. Implementa seguridad y compliance antes de usar con datos reales")
    print("3. Consulta el README.md para detalles técnicos")
    print()

if __name__ == "__main__":
    main()
