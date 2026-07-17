# Módulo de Ingesta y Clasificación Documental
## Guía de Uso y Ejemplos

⚠️ **AVISO IMPORTANTE**: Este módulo es una DEMO con datos ficticios. 
**NO debe usarse con datos reales de pacientes sin realizar una auditoría de seguridad y cumplimiento normativo completa.**

---

## Descripción General

El módulo de Ingesta y Clasificación Documental procesa documentación médica no estructurada (PDFs e imágenes) para:

1. **Leer** documentos en múltiples formatos
2. **Clasificar** automáticamente el tipo de documento
3. **Extraer** campos clínicos relevantes con confianza individual
4. **Validar** integridad y detectar inconsistencias
5. **Formatea** resultados como JSON estructurado

### Tipos de Documentos Soportados

- **formulario_diabetes**: Formulario estructurado de solicitud de medicación
- **laboratorio**: Estudios de laboratorio con resultados
- **prescripcion**: Recetas médicas con medicación prescripta
- **estudio_diagnostico**: Informes de estudios complementarios

---

## Instalación

```bash
# Clonar o descargar el proyecto
cd CodigoAuditoriaMedicaDiabetes

# Crear entorno virtual
python -m venv venv

# Activar entorno (Windows)
venv\Scripts\activate

# Activar entorno (Linux/Mac)
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

---

## Uso Básico

### Ejemplo 1: Procesar un Documento Individual

```python
from pathlib import Path
from src.document_reader import DocumentReader
from src.classifier import DocumentClassifier
from src.field_extractor import FieldExtractor
from src.output_formatter import OutputFormatter
import json

# Ruta al documento
doc_path = Path("tests/test_documents/formulario_diabetes/formulario_diabetes_sample.png")

# Step 1: Leer documento
reader = DocumentReader(use_ocr=False)  # use_ocr=True para documentos escaneados
text, images, metadata = reader.read_document(doc_path)

print(f"Documento leído: {metadata}")
print(f"Texto extraído: {text[:200]}...")

# Step 2: Clasificar documento
classifier = DocumentClassifier()
doc_type, confidence = classifier.classify_document(text, images, metadata)

print(f"\nClasificación: {doc_type}")
print(f"Confianza: {confidence}%")

# Step 3: Extraer campos
extractor = FieldExtractor()
fields = extractor.extract_fields(doc_type, text, images, metadata)

print(f"\nCampos extraídos:")
for field_name, field_data in fields.items():
    print(f"  {field_name}: {field_data['valor']} (confianza: {field_data['confianza']}%)")

# Step 4: Formatear resultado
formatter = OutputFormatter()
result = formatter.format_result(doc_type, confidence, fields, [])

print(f"\nJSON Result:")
print(json.dumps(result.to_json_dict(), indent=2, ensure_ascii=False))
```

**Salida esperada:**
```json
{
  "tipo_documento": "formulario_diabetes",
  "confianza_clasificacion": 92,
  "campos_extraidos": {
    "diagnostico": {
      "valor": "Diabetes Mellitus tipo 2",
      "confianza": 95
    },
    "medicacion_solicitada": {
      "valor": "Metformina 500mg, Enalapril 10mg",
      "confianza": 88
    },
    ...
  },
  "faltantes_o_inconsistencias": []
}
```

---

### Ejemplo 2: Procesar Múltiples Documentos

```python
from pathlib import Path
from src.document_reader import DocumentReader
from src.classifier import DocumentClassifier
from src.field_extractor import FieldExtractor
from src.output_formatter import OutputFormatter
import json

# Directorio con documentos de prueba
test_dir = Path("tests/test_documents")

# Procesar todos los documentos
results = []

for doc_type_dir in test_dir.iterdir():
    if doc_type_dir.is_dir():
        for doc_file in doc_type_dir.glob("*.png"):
            print(f"\nProcesando: {doc_file.name}")
            
            try:
                # Pipeline completo
                reader = DocumentReader(use_ocr=False)
                text, images, metadata = reader.read_document(doc_file)
                
                classifier = DocumentClassifier()
                doc_type, confidence = classifier.classify_document(text, images, metadata)
                
                extractor = FieldExtractor()
                fields = extractor.extract_fields(doc_type, text, images, metadata)
                
                formatter = OutputFormatter()
                result = formatter.format_result(doc_type, confidence, fields, [])
                
                results.append(result.to_json_dict())
                print(f"  ✓ Éxito - Tipo: {doc_type}")
                
            except Exception as e:
                print(f"  ✗ Error: {e}")

# Guardar resultados
output_file = Path("results.json")
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print(f"\nResultados guardados en: {output_file}")
```

---

## Interpretación de Resultados

### Estructura JSON Retornada

```json
{
  "tipo_documento": "string",           // Tipo clasificado del documento
  "confianza_clasificacion": 0-100,     // Confianza general de clasificación
  "campos_extraidos": {
    "nombre_campo": {
      "valor": "string",                // Valor extraído (o "NOT_FOUND")
      "confianza": 0-100                // Confianza individual del campo
    }
  },
  "faltantes_o_inconsistencias": []     // Lista de problemas detectados
}
```

### Confianza de Clasificación (0-100)

- **85-100**: Clasificación muy segura - confianza alta
- **70-84**: Clasificación probable - revisar si es necesario
- **50-69**: Clasificación incierta - revisar manualmente
- **< 50**: Clasificación muy incierta - requiere revisión

### Confianza de Campos (0-100)

- **90-100**: Campo muy legible y extraído con certeza
- **70-89**: Campo legible con buena confianza
- **50-69**: Campo parcialmente legible o ambiguo
- **0-49**: Campo ilegible o no encontrado
- **0**: Campo no encontrado (valor = "NOT_FOUND")

### Problemas Detectados

Ejemplos de inconsistencias reportadas:
- "Firma del médico no detectada"
- "Fecha vencida detectada"
- "Campo obligatorio ilegible: diagnostico"
- "Calidad de imagen muy baja (resolución < 200x200)"

---

## Parámetros Configurables

### DocumentReader

```python
reader = DocumentReader(
    use_ocr=True  # True: usar OCR para documentos escaneados
                  # False: solo extracción de texto (más rápido)
)
```

### FieldExtractor

```python
extractor = FieldExtractor()
# El extractor automáticamente detecta:
# - Campos requeridos según tipo de documento
# - Campos opcionales
# - Legibilidad del texto
# - Calidad de imagen
```

---

## Flujo de Procesamiento Completo

```
┌─────────────────────────────────────────┐
│ Documento (PDF o Imagen)                │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│ DocumentReader                          │
│ - Extrae texto                          │
│ - Realiza OCR si es necesario           │
│ - Recopila metadatos                    │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│ DocumentClassifier                      │
│ - Clasifica tipo de documento           │
│ - Asigna confianza de clasificación     │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│ FieldExtractor                          │
│ - Extrae campos por tipo                │
│ - Asigna confianza individual           │
│ - Evalúa legibilidad                    │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│ Validator                               │
│ - Verifica integridad                   │
│ - Detecta inconsistencias               │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│ OutputFormatter                         │
│ - Genera JSON estructurado              │
│ - Valida esquema                        │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│ JSON Result                             │
│ {                                       │
│   "tipo_documento": "...",              │
│   "confianza_clasificacion": 92,        │
│   "campos_extraidos": {...},            │
│   "faltantes_o_inconsistencias": [...]  │
│ }                                       │
└─────────────────────────────────────────┘
```

---

## Casos de Uso Comunes

### Caso 1: Validar Solicitud de Medicación

```python
# Procesar formulario de diabetes
result = process_document("solicitud_diabetes.png")

if result['confianza_clasificacion'] < 70:
    print("⚠️ Confianza baja - requiere revisión manual")
elif 'medicacion_solicitada' not in result['campos_extraidos']:
    print("❌ Medicación no encontrada")
elif result['campos_extraidos']['medicacion_solicitada']['confianza'] < 80:
    print("⚠️ Medicación extraída con baja confianza")
else:
    print("✓ Solicitud válida")
```

### Caso 2: Detectar Documentos Incompletos

```python
result = process_document("documento.png")
issues = result['faltantes_o_inconsistencias']

if issues:
    print("Documentación incompleta:")
    for issue in issues:
        print(f"  - {issue}")
else:
    print("Documentación completa")
```

### Caso 3: Auditoría de Campos Críticos

```python
result = process_document("documento.png")
campos = result['campos_extraidos']

campos_criticos = ['diagnostico', 'medicacion_solicitada', 'datos_medico']

for campo in campos_criticos:
    if campo not in campos or campos[campo]['confianza'] < 90:
        print(f"⚠️ Campo crítico con baja confianza: {campo}")
```

---

## Manejo de Errores

```python
from src.document_reader import DocumentReader
from src.error_handler import ErrorHandler

error_handler = ErrorHandler()

try:
    reader = DocumentReader()
    text, images, metadata = reader.read_document("documento.pdf")
except FileNotFoundError:
    error_handler.handle_error(
        "Archivo no encontrado",
        raise_error=True
    )
except Exception as e:
    error_handler.handle_error(
        f"Error al procesar documento: {e}",
        raise_error=False  # Registrar pero continuar
    )
```

---

## Características Clave

### ✓ Extracción Multimodal
- Soporta texto impreso y manuscrito
- Maneja documentos escaneados con OCR
- Procesa múltiples formatos (PDF, PNG, JPG)

### ✓ Confianza Individual por Campo
- No un score único del documento
- Cada campo tiene su propia confianza
- Refleja legibilidad real de datos

### ✓ Detección de Problemas
- Identifica campos ilegibles
- Detecta fechas vencidas
- Marca documentación incompleta
- Evalúa calidad de imagen

### ✓ Output JSON Estructurado
- Compatible con sistemas downstream
- Schema validado
- Fácil de parsear y almacenar

---

## Limitaciones y Notas

⚠️ **DEMO ONLY - No usar con datos reales sin:**
- Auditoría de seguridad completa
- Validación de compliance (HIPAA, GDPR, etc.)
- Cifrado de datos en tránsito y almacenamiento
- Registro de acceso y auditoría
- Anonimización de información sensible

### Rendimiento
- Documentos de buena calidad: 95%+ de precisión
- Documentos escaneados: Precisión depende de OCR
- Documentos bajos en calidad: Requieren revisión manual

### Versión Actual
- Modelo: Claude 3.5 Sonnet
- Versión: 1.0 (Demo)
- Última actualización: 2024

---

## Soporte Técnico

Para preguntas o issues:
1. Revisar esta guía
2. Consultar el README.md
3. Examinar test_results.json para ejemplos de salida
4. Revisar validation_results.json para detalles técnicos

---

## Renovación de Tratamiento: Carga y Validación de Documentos

El sistema incluye un flujo de renovación que permite al afiliado cargar la documentación requerida, recibe retroalimentación inmediata y bloquea el envío hasta que la solicitud esté completa y válida.

### Documentos requeridos (RENOVACION_DIABETES)

- **FORMULARIO_RENOVACION**: formulario_diabetes (1 documento, obligatorio)
- **ESTUDIOS_LABORATORIO**: laboratorio (hasta 5, obligatorio; se permiten distintos estudios)
- **PRESCRIPCION_MEDICA**: prescripcion (1 documento, obligatorio)
- **ESTUDIO_DIAGNOSTICO**: estudio_diagnostico (hasta 2, obligatorio; se permiten distintos estudios)

### Endpoints de la API de renovación

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/renovacion/solicitudes` | Crea una solicitud en estado `BORRADOR` |
| POST | `/api/renovacion/solicitudes/<id>/documentos` | Sube un documento para un requerimiento y devuelve validación inmediata |
| GET | `/api/renovacion/solicitudes/<id>/validar` | Devuelve el resultado de validación actual |
| POST | `/api/renovacion/solicitudes/<id>/enviar` | Envía a auditoría solo si `can_submit=True` |
| DELETE | `/api/renovacion/solicitudes/<id>/documentos/<doc_id>` | Elimina un documento y revalida |
| GET | `/api/renovacion/catalogo/RENOVACION_DIABETES` | Devuelve el catálogo de requerimientos |

### Estados de una solicitud de renovación

- `BORRADOR`: solicitud recién creada
- `DOCS_EN_CARGA`: se subió al menos un documento
- `DOCS_INCOMPLETAS`: faltan documentos obligatorios o hay duplicados que bloquean el envío
- `DOCS_WARNING_CALIDAD`: solo hay advertencias de calidad (no bloquea)
- `LISTA_PARA_ENVIO`: solicitud lista para enviar a auditoría
- `EN_AUDITORIA`: solicitud enviada correctamente

### Comportamiento de validación

- Documentación faltante → **bloquea el envío**.
- Documentos duplicados que exceden el límite o reemplazan un documento obligatorio → **bloquean el envío**.
- Advertencias de calidad de imagen/legibilidad → se informan, pero **permiten continuar**.
- Si se detecta que un documento cargado como un requerimiento realmente corresponde a otro tipo, se emite una advertencia de clasificación.
- Solo las solicitudes con `can_submit=True` pueden pasar a `EN_AUDITORIA`.

### Ejemplo: crear, cargar y enviar una solicitud válida

```bash
# 1. Crear solicitud
curl -X POST http://127.0.0.1:5000/api/renovacion/solicitudes \
  -H "Content-Type: application/json" \
  -d '{"affiliate_id":"A123"}'

# 2. Subir cada documento requerido
curl -X POST http://127.0.0.1:5000/api/renovacion/solicitudes/<SOL_ID>/documentos \
  -F "requirement_id=FORMULARIO_RENOVACION" \
  -F "document=@formulario.png"

# 3. Enviar a auditoría cuando esté lista
curl -X POST http://127.0.0.1:5000/api/renovacion/solicitudes/<SOL_ID>/enviar
```

### Ejecución de tests de renovación

```bash
# Tests unitarios del motor de validación
python tests/test_renewal_validation.py

# Tests de integración de la API y flujo de auditoría
python tests/test_renewal_api_integration.py

# Compilación de todos los módulos
python -m py_compile src/renewal_*.py web_app.py tests/test_renewal_*.py
```

## Próximos Pasos

1. **Generar un lote**: Procesar múltiples documentos y almacenar resultados
2. **Integración**: Conectar con sistemas de auditoría existentes
3. **Customización**: Ajustar campos según requisitos específicos
4. **Productización**: Implementar seguridad y compliance completos
