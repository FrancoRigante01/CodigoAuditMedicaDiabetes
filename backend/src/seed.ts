import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

async function main() {
  await prisma.auditReview.deleteMany();
  await prisma.comment.deleteMany();
  await prisma.document.deleteMany();
  await prisma.patient.deleteMany();

  const patients = [
    {
      name: "Juan Pérez",
      dni: "25444333",
      age: 45,
      plan: "Plan Global",
      tipoTramite: "Empadronamiento Inicial",
      clinical_history: "Diabetes Tipo 2 diagnosticada hace 5 años.",
      status: "PENDIENTE"
    },
    {
      name: "María Gómez",
      dni: "30111222",
      age: 38,
      plan: "Plan Básico",
      tipoTramite: "Renovación",
      clinical_history: "Diabetes Tipo 1 desde los 12 años.",
      status: "APROBADO"
    },
    {
      name: "Carlos Sanchez",
      dni: "18555777",
      age: 65,
      plan: "Plan PMI (Jubilado)",
      tipoTramite: "Empadronamiento Inicial",
      clinical_history: "Reciente diagnóstico de Diabetes Tipo 2. Obesidad.",
      status: "PENDIENTE"
    },
    {
      name: "Laura Rodriguez",
      dni: "41222999",
      age: 26,
      plan: "Plan Joven",
      tipoTramite: "Empadronamiento Inicial",
      clinical_history: "Diabetes Tipo 1.",
      status: "PENDIENTE"
    }
  ];

  for (const p of patients) {
    await prisma.patient.create({ data: p });
  }

  console.log('Base de datos poblada con éxito');
}

main()
  .catch(e => {
    console.error(e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
