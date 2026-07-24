import express from 'express';
import multer from 'multer';
import { PrismaClient } from '@prisma/client';
import { MedicalDocumentProcessor } from '../services/processor';

const router = express.Router({ mergeParams: true });
const prisma = new PrismaClient();
const processor = new MedicalDocumentProcessor();

const storage = multer.diskStorage({
  destination: function (req, file, cb) {
    cb(null, './uploads/') // Ensure this directory exists
  },
  filename: function (req, file, cb) {
    cb(null, Date.now() + '-' + file.originalname)
  }
});
const upload = multer({ storage: storage });

router.post('/', upload.array('documents'), async (req, res) => {
  const patientId = req.params.id; // comes from /api/patients/:id/documents

  if (!req.files || (req.files as Express.Multer.File[]).length === 0) {
    return res.status(400).json({ error: 'No files uploaded' });
  }

  try {
    const files = req.files as Express.Multer.File[];
    const uploadedDocs = [];

    // 1. Process and save each new document
    for (const file of files) {
      const rawText = await processor.extractTextFromFile(file.path);
      const dynamicScore = await processor.evaluateReliability(rawText);
      
      const doc = await prisma.document.create({
        data: {
          patientId: parseInt(patientId as string),
          filename: file.originalname,
          filePath: file.path,
          docType: "Documento Médico",
          extractedText: rawText,
          reliabilityScore: dynamicScore,
          status: "CARGADO"
        } as any
      });
      uploadedDocs.push(doc);
    }

    // 2. Fetch all active documents for this patient to combine them
    const allPatientDocs = await prisma.document.findMany({
      where: { patientId: parseInt(patientId as string), isArchived: false }
    });

    const allTexts = allPatientDocs
      .map((d: any) => d.extractedText)
      .filter((t): t is string => !!t);

    // 3. Evaluate all active documents together
    if (allTexts.length > 0) {
      const patient = await prisma.patient.findUnique({
        where: { id: parseInt(patientId as string) }
      });
      const result = await processor.evaluateMultipleDocuments(allTexts, patient);

      if (result.veredicto_auditoria) {
        const activeReview = await prisma.auditReview.findFirst({
          where: { patientId: parseInt(patientId as string), isArchived: false }
        });

        const dataToUpdate = {
          aiSuggestion: result.justificacion_auditoria,
          aiConfidence: result.confianza_clasificacion / 100.0,
          extractedData: result.extractedData ? JSON.stringify(result.extractedData) : null
        };

        if (activeReview) {
           await prisma.auditReview.update({
             where: { id: activeReview.id },
             data: dataToUpdate
           });
        } else {
           await prisma.auditReview.create({
             data: {
               patientId: parseInt(patientId as string),
               isArchived: false,
               ...dataToUpdate
             }
           });
        }
      }
    }

    res.json({
      message: `${files.length} document(s) uploaded and evaluated successfully`,
      documents: uploadedDocs
    });
  } catch (error: any) {
    console.error("Processing error", error);
    res.status(500).json({ error: error.message });
  }
});

export default router;
