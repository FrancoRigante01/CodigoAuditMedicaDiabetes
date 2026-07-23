import os
from PIL import Image, ImageDraw, ImageFont

def generate_doc(filename, lines):
    # Crear una imagen blanca de 800x600
    img = Image.new('RGB', (800, 600), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    
    # Intentar cargar una fuente por defecto
    try:
        font = ImageFont.truetype("arial.ttf", 24)
    except IOError:
        font = ImageFont.load_default()

    y_text = 50
    for line in lines:
        d.text((50, y_text), line, fill=(0, 0, 0), font=font)
        y_text += 40

    img.save(filename)
    print(f"Generated {filename}")

if __name__ == "__main__":
    tests_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 1. Aprobación Completa
    generate_doc(os.path.join(tests_dir, "1_aprobacion_completa.png"), [
        "FORMULARIO DIABETES - RENOVACION",
        "Paciente: Juan Perez",
        "Diagnóstico: Diabetes Tipo 2",
        "Años de evolución: 5",
        "Medicación: Metformina 500mg, 1 comprimido c/12hs.",
        "Laboratorio: Glucemia 110 mg/dl, HbA1c 6.5%",
        "Firma y Sello: Dr. Roberto Martínez, MP-12345",
        "Fecha: 22/07/2026 - VIGENTE"
    ])
    
    # 2. Aprobación Parcial
    generate_doc(os.path.join(tests_dir, "2_aprobacion_parcial.png"), [
        "FORMULARIO DIABETES",
        "Paciente: Maria Garcia",
        "Diagnóstico: Diabetes Tipo 1",
        "Medicación solicitada: Insulina Glargina",
        "Estudios: Adjunta laboratorio reciente.",
        "OBSERVACION: La firma del médico tratante está algo borrosa.",
        "Fecha: 15/07/2026"
    ])
    
    # 3. Rechazo
    generate_doc(os.path.join(tests_dir, "3_rechazo.png"), [
        "SOLICITUD INCOMPLETA",
        "Paciente: Carlos Lopez",
        "Diagnóstico: No especificado claramente.",
        "Medicación solicitada: Tiras reactivas.",
        "Falta firma del médico.",
        "Laboratorio: Vencido (año 2022)."
    ])
    
    # 4. Solicitar Info Adicional
    generate_doc(os.path.join(tests_dir, "4_solicitar_info.png"), [
        "PRESCRIPCION MEDICA",
        "Paciente: Ana Gomez",
        "Diagnóstico: Diabetes",
        "Medicación solicitada: Insulina Aspart",
        "ATENCION: No se especifica la dosis diaria ni la vigencia de la receta.",
        "Firma: Dra. Lopez, MP-54321"
    ])
