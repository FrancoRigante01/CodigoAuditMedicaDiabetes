# Módulo de Ingesta y Clasificación Documental para Auditoría Médica

## ⚠️ ADVERTENCIA CRÍTICA - DEMO ONLY

**Este módulo es una DEMOSTRACIÓN con DATOS FICTICIOS ÚNICAMENTE.**

**NO debe ser utilizado con datos reales de pacientes sin:**
1. Revisión exhaustiva de seguridad y compliance
2. Implementación de controles HIPAA/LGPD según jurisdicción
3. Validación clínica independiente por profesionales médicos calificados
4. Auditoría de ciberseguridad y certificación
5. Consentimiento informado de pacientes y profesionales

Este código está diseñado exclusivamente para demostración y propósitos educativos.

---

## 📋 Descripción General

Módulo de procesamiento de documentación médica para un caso de uso de auditoría en diabetes. Recibe documentación no estructurada (PDF, imágenes) y realiza:

1. **Lectura multimodal**: Extrae contenido de PDFs escaneados, imágenes manuscritas e impresas
2. **Clasificación automática**: Identifica tipo de documento (formulario diabetes, laboratorio, prescripción, estudio diagnóstico)
3. **Extracción de campos**: Obtiene información relevante según tipo de documento
4. **Scoring de confianza**: Asigna confianza individual a cada campo extraído
5. **Detección de inconsistencias**: Identifica campos faltantes, fechas vencidas, o problemas de legibilidad

---

## 🏗️ Arquitectura

```
src/
├── __init__.py                 # Módulo principal
├── models.py                   # Estructuras de datos y esquemas
├── document_reader.py          # Lectura de documentos (PDF/imágenes)
├── document_classifier.py      # Clasificación automática de tipos
├── field_extractor.py          # Extracción de campos relevantes
├── validation.py               # Validación y detección de inconsistencias
└── processor.py                # Orquestación del pipeline completo

test_documents/                 # Documentos ficticios para pruebas
├── formulario_diabetes_1.png
├── laboratorio_1.png
├── prescripcion_1.png
└── estudio_diagnostico_1.png

examples/
├── usage_example.py            # Ejemplo de uso
└── demo_script.py              # Script de demostración completo
```

---

## 🚀 Configuración

### 1. Requisitos Previos
- Python 3.8+
- pip
- API key de Anthropic Claude (para visión multimodal)

### 2. Instalación

```bash
# Crear entorno virtual
python -m venv venv
python -m venv /c/venv/auditmed # Si sale error un error de que la ruta es muy larga

#Activar entorno virtual
source venv/bin/activate  # En Windows: venv\Scripts\activate
source /c/venv/auditmed/Scripts/activate # Si sale error un error de que la ruta es muy larga

# Instalar dependencias
pip install -r requirements.txt
```

### 3. Configuración de API Keys

Crear archivo `.env` en la raíz del proyecto:

```env
ANTHROPIC_API_KEY=your_api_key_here
```

**NO commitar el archivo `.env` a control de versiones.**

---

## 📖 Uso

### Uso Básico

```python
from src.processor import MedicalDocumentProcessor

# Inicializar procesador
processor = MedicalDocumentProcessor()

# Procesar documento
result = processor.process_document("ruta/a/documento.pdf")

# Resultado en formato JSON
print(result.model_dump_json(indent=2))
```

### Interfaz Web

El proyecto incluye una interfaz web de demo en `templates/index.html` servida por Flask:

```bash
python web_app.py
```

Luego abrir en el navegador:

```text
http://127.0.0.1:5000
```

> **Nota:** No abrir `templates/index.html` directamente con doble clic, porque el navegador usará el protocolo `file://` y el envío del formulario fallará por políticas CORS. Siempre acceder a través del servidor Flask.

### Formato de Salida

```json
{
  "tipo_documento": "formulario_diabetes",
  "confianza_clasificacion": 85,
  "campos_extraidos": {
    "diagnostico": {
      "valor": "Diabetes tipo 2",
      "confianza": 90
    },
    "medicacion_solicitada": {
      "valor": "Metformina 500mg",
      "confianza": 85
    },
    "tipo_diabetes": {
      "valor": "Tipo 2",
      "confianza": 92
    },
    "fecha_firma": {
      "valor": "2024-06-15",
      "confianza": 88
    },
    "datos_medico_tratante": {
      "valor": "Dr. Juan Pérez, Matrícula 12345",
      "confianza": 82
    }
  },
  "faltantes_o_inconsistencias": [
    "Insumo solicitado: campo no detectado",
    "Firma del médico parcialmente ilegible"
  ]
}
```

---

## 📚 Tipos de Documentos

### 1. formulario_diabetes
Formulario estructurado firmado por médico tratante.

**Campos requeridos:**
- diagnóstico
- tipo_diabetes
- medicación_solicitada
- fecha_firma
- datos_medico_tratante

**Campos opcionales:**
- insumo_solicitado
- notas_medico

### 2. laboratorio
Estudios de laboratorio con resultados.

**Campos requeridos:**
- tipo_estudio
- fecha_estudio
- valores_relevantes

**Campos opcionales:**
- laboratorio_nombre
- medico_solicitante

### 3. prescripcion
Prescripción médica de medicamentos o insumos.

**Campos requeridos:**
- medicacion_insumo
- dosis
- vigencia_receta
- matricula_prescriptor

**Campos opcionales:**
- nombre_prescriptor
- indicaciones

### 4. estudio_diagnostico
Informes médicos y estudios complementarios.

**Campos requeridos:**
- tipo_informe
- fecha_informe
- conclusion_relevante

**Campos opcionales:**
- medico_responsable
- modalidad_estudio

---

## 🧪 Pruebas

Ejecutar suite de pruebas con documentos ficticios:

```bash
python examples/demo_script.py
```

Esto procesa ejemplos de cada tipo de documento y muestra resultados formateados.

---

## 📊 Interpretación de Scores de Confianza

- **90-100**: Texto claro, bien formado, sin ambigüedad
- **75-89**: Texto legible con algunas secciones borrosas o tachadas
- **50-74**: Texto parcialmente ilegible, campo incompleto, o multiple interpretations posibles
- **0-49**: Contenido muy ilegible, incierto, o inferido con baja confianza
- **0**: Campo no detectado

---

## ⚙️ Configuración Avanzada

### Logging

```python
from src.processor import MedicalDocumentProcessor
import logging

# Habilitar debug logging
logging.basicConfig(level=logging.DEBUG)
processor = MedicalDocumentProcessor(verbose=True)
```

### Procesamiento por Lotes

```python
import os
from src.processor import MedicalDocumentProcessor

processor = MedicalDocumentProcessor()

for filename in os.listdir("documents/"):
    if filename.endswith((".pdf", ".png", ".jpg")):
        result = processor.process_document(f"documents/{filename}")
        print(f"\n{filename}: {result.tipo_documento}")
```

---

## 🔒 Notas de Seguridad y Compliance

### Para Uso en Producción

Si planea usar este módulo con datos reales de pacientes:

1. **Cumplimiento Legal**: Verificar HIPAA (USA), LGPD (Brasil), LOPD (España), etc.
2. **Encriptación**: Implementar encriptación en tránsito y en reposo
3. **Auditoría**: Registrar accesos y cambios con trazabilidad completa
4. **Validación clínica**: Todos los resultados deben ser revisados por médicos cualificados
5. **Control de acceso**: Implementar autenticación y autorización robustas
6. **Backup y recuperación**: Plan de continuidad y recuperación ante desastres
7. **Certifications**: ISO 27001, SOC 2, u otras relevantes para tu jurisdicción

### Limitaciones Conocidas

- No valida integridad digital de documentos originales
- No integra con sistemas de historia clínica electrónica
- No reemplaza revisión médica profesional
- Puede fallar con documentos de muy baja calidad
- No maneja documentos multiidioma complejos

---

## 📝 Licencia y Responsabilidad

Este código se proporciona "TAL CUAL" para propósitos educativos y de demostración.

**Los autores no se hacen responsables por:**
- Daño a pacientes por uso inadecuado
- Incumplimiento normativo
- Pérdida de datos
- Cualquier consecuencia de usar este código en producción sin revisión completa

---

## 📧 Soporte

Para problemas o sugerencias en el contexto de DEMO, abrir issue en el repositorio.

**NUNCA reportar datos reales de pacientes en issues públicos.**

---

## Última Actualización

Julio 2024 - DEMO Version 0.1.0
