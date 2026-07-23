const { createCanvas } = require('canvas');
const fs = require('fs');
const path = require('path');

const outputDir = path.join(require('os').homedir(), 'OneDrive - Softtek', 'Desktop');

const cases = [
  {
    filename: '1_aprobacion_completa.png',
    text: `CERTIFICADO MÉDICO - DIABETES

Paciente: Juan Pérez
DNI: 25.444.333

Diagnóstico: Diabetes Mellitus tipo 2
Medicamento solicitado: Metformina 500mg - 1 comprimido c/12hs.

Firma y Sello del Médico: Dr. García - MN 12345`
  },
  {
    filename: '2_aprobacion_parcial.png',
    text: `CERTIFICADO MÉDICO - DIABETES

Paciente: María Gómez
DNI: 30.111.222

Diagnóstico: Diabetes Mellitus tipo 1
Medicamento solicitado: Insulina NPH

Firma y Sello del Médico: ILEGIBLE - SIN SELLO VALIDO`
  },
  {
    filename: '3_rechazo.png',
    text: `CERTIFICADO MÉDICO - CLINICA GENERAL

Paciente: Carlos López
DNI: 35.123.456

Diagnóstico: Resfriado común, cefalea y malestar general. No presenta patología crónica.
Medicamento solicitado: Ibuprofeno 400mg. Reposo por 48hs.

Firma y Sello del Médico: Dr. Fernández - MN 98765`
  },
  {
    filename: '4_solicitar_info.png',
    text: `RECETA MÉDICA

Paciente: Ana Martínez
DNI: 28.555.666

Medicamento solicitado: Tiras reactivas Accu-Chek (Caja x 50) y Lancetas.

Nota: Falta especificar el diagnóstico exacto en el formulario para poder procesar el pedido.

Firma y Sello del Médico: Dra. Silva - MN 54321`
  }
];

cases.forEach((c) => {
  const canvas = createCanvas(800, 600);
  const ctx = canvas.getContext('2d');

  // Background
  ctx.fillStyle = '#ffffff';
  ctx.fillRect(0, 0, 800, 600);

  // Border
  ctx.strokeStyle = '#000000';
  ctx.lineWidth = 2;
  ctx.strokeRect(10, 10, 780, 580);

  // Text
  ctx.fillStyle = '#000000';
  ctx.font = '24px Arial';
  ctx.textBaseline = 'top';

  const lines = c.text.split('\n');
  let y = 50;
  lines.forEach(line => {
    ctx.fillText(line, 50, y);
    y += 40;
  });

  const buffer = canvas.toBuffer('image/png');
  const outPath = path.join(outputDir, c.filename);
  fs.writeFileSync(outPath, buffer);
  console.log('Generado:', outPath);
});
