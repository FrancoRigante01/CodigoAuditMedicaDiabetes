"""
Script to generate fictional test documents for module testing.
Creates sample documents for each document type.
"""

from pathlib import Path
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
import io


def create_test_documents_dir():
    """Create test documents directory structure."""
    test_dir = Path(__file__).parent / "test_documents"
    test_dir.mkdir(exist_ok=True)
    
    # Create subdirectories for each document type
    (test_dir / "formulario_diabetes").mkdir(exist_ok=True)
    (test_dir / "laboratorio").mkdir(exist_ok=True)
    (test_dir / "prescripcion").mkdir(exist_ok=True)
    (test_dir / "estudio_diagnostico").mkdir(exist_ok=True)
    
    return test_dir


def create_image_with_text(width: int, height: int, text: str, filename: str) -> str:
    """Create an image with text content."""
    # Create image with white background
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    # Use default font (we'll use a simple default)
    try:
        font = ImageFont.truetype("arial.ttf", 12)
    except (IOError, OSError):
        font = ImageFont.load_default()
    
    # Draw text
    draw.text((20, 20), text, fill='black', font=font)
    
    # Save image
    img.save(filename)
    return filename


def create_formulario_diabetes() -> str:
    """Create a fictional diabetes form document."""
    test_dir = create_test_documents_dir()
    filename = test_dir / "formulario_diabetes" / "formulario_diabetes_sample.png"
    
    text = """FORMULARIO DE SOLICITUD DE MEDICACIÓN - DIABETES
Ministerio de Salud - Auditoría Médica

DATOS DEL PACIENTE
Nombre: Juan Carlos Pérez García
Documento: 12345678
Fecha de Nacimiento: 15/03/1965
Teléfono: 011-4567-8901

DIAGNÓSTICO MÉDICO
Diagnóstico Principal: Diabetes Mellitus tipo 2
Tiempo de Evolución: 8 años
Comorbilidades: Hipertensión Arterial, Dislipidemia

MEDICACIÓN SOLICITADA
Medicamento 1: Metformina 500mg
Dosis: 2 comprimidos cada 8 horas
Duración: 6 meses

Medicamento 2: Enalapril 10mg
Dosis: 1 comprimido cada 12 horas
Duración: 6 meses

INSUMOS SOLICITADOS
Tiras reactivas para glucómetro: 100 tiras
Lancetas para punción: 100 lancetas
Glucómetro (de ser necesario): No aplica

DATOS DEL MÉDICO TRATANTE
Nombre: Dr. Roberto Martínez López
Matrícula: MP-2024-001567
Especialidad: Endocrinología
Teléfono Consultorio: 011-2345-6789

FIRMA Y SELLO
Fecha: 12/07/2024
Firma del Médico: ___________________
Sello de Consultorio: [SELLO]
"""
    
    return create_image_with_text(800, 1100, text, str(filename))


def create_laboratorio() -> str:
    """Create a fictional laboratory report document."""
    test_dir = create_test_documents_dir()
    filename = test_dir / "laboratorio" / "laboratorio_sample.png"
    
    text = """LABORATORIO CLÍNICO "DIAGNÓSTICO INTEGRAL"
Av. Corrientes 1234, Buenos Aires

INFORME DE LABORATORIO

Paciente: María López Fernández
Documento: 87654321
Fecha de Análisis: 08/07/2024
Fecha de Informe: 10/07/2024

DATOS CLÍNICOS
Médico Solicitante: Dra. Laura Gómez
Diagnóstico Clínico: Control de Diabetes Mellitus tipo 2

RESULTADOS DE ANÁLISIS

Glucemia en Ayunas: 145 mg/dL (Normal: 70-100)
Hemoglobina Glicosilada (HbA1c): 7.8% (Normal: <5.7)
Creatinina: 0.9 mg/dL (Normal: 0.7-1.3)
Urea: 35 mg/dL (Normal: 15-45)

Glucosa Post Prandial (2 hs): 182 mg/dL (Normal: <140)

PERFIL LIPÍDICO
Colesterol Total: 245 mg/dL (Deseable: <200)
LDL Colesterol: 165 mg/dL (Deseable: <100)
HDL Colesterol: 38 mg/dL (Deseable: >40)
Triglicéridos: 185 mg/dL (Normal: <150)

OBSERVACIONES
Control de glucosa insuficiente. Se recomienda ajuste 
de medicación. Paciente debe mantener dieta hipoglucdica
y aumentar actividad física.

PROFESIONAL RESPONSABLE
Bioquímico: Lic. Carlos Mendoza
Matrícula: BQ-5678-LP
Fecha: 10/07/2024
Firma: ___________________
"""
    
    return create_image_with_text(800, 1100, text, str(filename))


def create_prescripcion() -> str:
    """Create a fictional prescription document."""
    test_dir = create_test_documents_dir()
    filename = test_dir / "prescripcion" / "prescripcion_sample.png"
    
    text = """RECETA MÉDICA - MEDICAMENTO SUJETO A DISPENSACIÓN CONTROLADA

Consultorio Médico "Endocrinología Moderna"
Calle Rivadavia 567 - Buenos Aires

Paciente: Diego Ramírez González
Documento: 34567890
Fecha: 14/07/2024
Vigencia: 30 días (Válida hasta: 13/08/2024)

MEDICAMENTOS PRESCRITOS

1) METFORMINA 850 mg
   Cantidad: 60 comprimidos
   Posología: 1 comprimido cada 12 horas (con comidas)
   Indicación: Diabetes Mellitus tipo 2
   Duración: 30 días

2) BROMOCRIPTINA 2.5 mg
   Cantidad: 30 comprimidos
   Posología: 1/2 comprimido en la mañana con el desayuno
   Indicación: Efectos secundarios metabólicos
   Duración: 30 días

INDICACIONES ESPECIALES
- Tomar siempre con alimentos
- No ingerir alcohol durante el tratamiento
- Control de glucemia cada 7 días
- Consulta de seguimiento en 30 días

DATOS DEL PRESCRIPTOR
Nombre: Dr. Fernando Álvarez López
Matrícula: MP-1985-002456
CUIT: 20-12345678-9
Especialidad: Endocrinología
Teléfono: 011-3456-7890
E-mail: fernando.alvarez@medicina.ar

FIRMA Y SELLO
Firma del Médico: ___________________
Aclaración: Dr. Fernando Álvarez López
Sello: [SELLO PROFESIONAL]

OBSERVACIONES FARMACÉUTICAS
(Completado por la farmacia)
Farmacéutico: ___________________
Fecha de Dispensación: ___________
"""
    
    return create_image_with_text(800, 1200, text, str(filename))


def create_estudio_diagnostico() -> str:
    """Create a fictional diagnostic study report document."""
    test_dir = create_test_documents_dir()
    filename = test_dir / "estudio_diagnostico" / "estudio_diagnostico_sample.png"
    
    text = """INFORME DE ESTUDIO - ECOCARDIOGRAFÍA

Instituto de Cardiología y Medicina Vascular
Esmeralda 456 - Piso 8 - Buenos Aires

DATOS DEL PACIENTE
Nombre: Patricia González Rodríguez
Documento: 23456789
Edad: 58 años
Género: Femenino
Fecha de Estudio: 11/07/2024

MOTIVO DEL ESTUDIO
Control cardiológico en paciente con Diabetes Mellitus 
tipo 2 y Hipertensión Arterial.

TÉCNICA EMPLEADA
Ecocardiografía transtorácica bidimensional con Doppler
Equipo: Philips iE 33 - Transductor 3.5 MHz

HALLAZGOS PRINCIPALES

AURÍCULA DERECHA:
Diámetro normal: 45 mm
Sin dilatación apreciable

VENTRÍCULO DERECHO:
Diámetro basal: 35 mm
Función sistólica: Normal
TAPSE: 22 mm

AURÍCULA IZQUIERDA:
Diámetro: 42 mm
Volumen: 58 mL
Función: Normal

VENTRÍCULO IZQUIERDO:
Dimensión diastólica: 52 mm
Espesor de pared: Normal
Función sistólica: Normal (FE 62%)
Strain global: -18%

VÁLVULAS CARDÍACAS:
Válvula mitral: Normal, sin insuficiencia
Válvula tricúspidea: Normal
Válvula aórtica: Normal
Válvula pulmonar: Normal

PRESIÓN SISTÓLICA DE ARTERIA PULMONAR: 28 mmHg (Normal)

CONCLUSIÓN
Corazón de tamaño normal. Función sistólica y diastólica 
del ventrículo izquierdo conservadas. No se observan 
valvulopatías significativas. Presión pulmonar normal.
Estudio sin hallazgos patológicos relevantes.

MÉDICO CARDIÓLOGO RESPONSABLE
Dr. Alejandro Ruiz Domínguez
Matrícula: MP-1988-003789
Especialidad: Cardiología
Fecha: 11/07/2024
Firma: ___________________
"""
    
    return create_image_with_text(800, 1200, text, str(filename))


def create_low_quality_document() -> str:
    """Create a low-quality document for testing legibility handling."""
    test_dir = create_test_documents_dir()
    filename = test_dir / "formulario_diabetes" / "formulario_low_quality.png"
    
    # Create a very small, low contrast image
    img = Image.new('RGB', (300, 400), color=(200, 200, 200))
    draw = ImageDraw.Draw(img)
    
    text = """FORM DIABETES - HANDWRITTEN
Name: XXX? - unclear
Date: ???
Med: Metforrr... illegible
Doctor: [illegible signature]
"""
    
    try:
        font = ImageFont.truetype("arial.ttf", 8)
    except (IOError, OSError):
        font = ImageFont.load_default()
    
    draw.text((5, 5), text, fill=(220, 220, 220), font=font)
    img.save(filename)
    return str(filename)


def main():
    """Generate all test documents."""
    print("Creating fictional test documents...")
    
    test_dir = create_test_documents_dir()
    print(f"Test documents directory: {test_dir}")
    
    # Create each document type
    print("\n1. Creating formulario_diabetes...")
    formulario_path = create_formulario_diabetes()
    print(f"   Created: {formulario_path}")
    
    print("\n2. Creating laboratorio...")
    laboratorio_path = create_laboratorio()
    print(f"   Created: {laboratorio_path}")
    
    print("\n3. Creating prescripcion...")
    prescripcion_path = create_prescripcion()
    print(f"   Created: {prescripcion_path}")
    
    print("\n4. Creating estudio_diagnostico...")
    estudio_path = create_estudio_diagnostico()
    print(f"   Created: {estudio_path}")
    
    print("\n5. Creating low-quality document...")
    low_quality_path = create_low_quality_document()
    print(f"   Created: {low_quality_path}")
    
    print("\n✓ All test documents created successfully!")
    print(f"\nTest documents are located in: {test_dir}")


if __name__ == "__main__":
    main()
