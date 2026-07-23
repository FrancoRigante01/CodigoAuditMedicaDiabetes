import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

async function main() {
  await prisma.patient.deleteMany();
  await prisma.document.deleteMany();
  await prisma.comment.deleteMany();
  await prisma.auditReview.deleteMany();

  const patients = [
    {
      name: "Juan Pérez",
      dni: "25444333",
      age: 45,
      clinical_history: "Diabetes Tipo 2 diagnosticada hace 5 años.",
      status: "PENDIENTE"
    },
    {
      name: "María Gómez",
      dni: "30111222",
      age: 38,
      clinical_history: "Diabetes Tipo 1 desde los 12 años.",
      status: "APROBADO"
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
