import express from 'express';
import { PrismaClient } from '@prisma/client';

const router = express.Router();
const prisma = new PrismaClient();

// Get all patients
router.get('/', async (req, res) => {
  const { status } = req.query;
  const patients = await prisma.patient.findMany({
    ...(status ? { where: { status: String(status) } } : {})
  });
  res.json(patients);
});

// Create a new patient
router.post('/', async (req, res) => {
  const { name, dni, age, clinical_history } = req.body;
  if (!name || !dni) {
    return res.status(400).json({ error: 'Name and DNI are required' });
  }
  try {
    const newPatient = await prisma.patient.create({
      data: {
        name,
        dni,
        ...(age !== undefined && age !== null && age !== '' ? { age: Number(age) } : {}),
        ...(clinical_history !== undefined ? { clinical_history } : {}),
        status: 'PENDIENTE'
      }
    });
    res.status(201).json(newPatient);
  } catch (error) {
    console.error('Error creating patient:', error);
    res.status(500).json({ error: 'Error creating patient', details: String(error) });
  }
});

// Get patient detail
router.get('/:id', async (req, res) => {
  const { id } = req.params;
  const patient = await prisma.patient.findUnique({
    where: { id: parseInt(id) },
    include: {
      documents: {
        orderBy: { uploadedAt: 'desc' }
      },
      comments: true,
      auditReviews: {
        orderBy: { reviewedAt: 'desc' }
      },
    }
  });

  if (!patient) {
    return res.status(404).json({ error: 'Patient not found' });
  }

  res.json(patient);
});

// Add comment
router.post('/:id/comments', async (req, res) => {
  const { id } = req.params;
  const { role, text } = req.body;

  if (!text) {
    return res.status(400).json({ error: 'No text provided' });
  }

  const comment = await prisma.comment.create({
    data: {
      patientId: parseInt(id),
      authorRole: role || 'MEDICO',
      text,
    }
  });

  res.json({ message: 'Comment added successfully', comment });
});

// Audit patient
router.post('/:id/audit', async (req, res) => {
  const { id } = req.params;
  const { action, notes } = req.body;

  let newStatus = 'PENDIENTE';
  if (action === 'APROBAR') newStatus = 'APROBADO';
  else if (action === 'APROBAR_PARCIAL') newStatus = 'APROBADO PARCIALMENTE';
  else if (action === 'RECHAZAR') newStatus = 'RECHAZADO';
  else if (action === 'REQUIERE_INFO') newStatus = 'REQUIERE INFO';

  const patientId = parseInt(id);

  await prisma.patient.update({
    where: { id: patientId },
    data: { status: newStatus }
  });

  const updateData: any = { finalVerdict: newStatus, auditorNotes: notes };
  if (action === 'RECHAZAR') {
    updateData.aiSuggestion = null;
    updateData.aiConfidence = null;
  }

  const activeReview = await prisma.auditReview.findFirst({
    where: { patientId, isArchived: false }
  });

  if (activeReview) {
    await prisma.auditReview.update({
      where: { id: activeReview.id },
      data: updateData
    });
  } else {
    await prisma.auditReview.create({
      data: { patientId, ...updateData }
    });
  }

  res.json({ message: `Patient ${newStatus}` });
});

// Renew patient documentation
router.post('/:id/renew', async (req, res) => {
  const { id } = req.params;
  const patientId = parseInt(id);

  try {
    await prisma.patient.update({
      where: { id: patientId },
      data: { status: 'RENOVACION_PENDIENTE' }
    });

    await prisma.document.updateMany({
      where: { patientId, isArchived: false },
      data: { isArchived: true }
    });

    await prisma.auditReview.updateMany({
      where: { patientId, isArchived: false },
      data: { isArchived: true }
    });

    res.json({ message: 'Patient renewed successfully' });
  } catch (error) {
    console.error('Error renewing patient:', error);
    res.status(500).json({ error: 'Error renewing patient' });
  }
});

export default router;
