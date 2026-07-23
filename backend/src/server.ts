import * as dotenv from 'dotenv';
import path from 'path';
// Cargar .env de la raíz del proyecto
dotenv.config({ path: path.resolve(__dirname, '../../.env') });
// Cargar .env local del backend si existe
dotenv.config();

import express from 'express';
import cors from 'cors';
import { PrismaClient } from '@prisma/client';
import patientRoutes from './routes/patients';
import documentRoutes from './routes/documents';

const app = express();
const port = process.env.PORT || 5000;

// Need to pass url for Prisma 7 client if using SQLite file directly
export const prisma = new PrismaClient({
  datasources: {
    db: {
      url: 'file:./dev.db',
    },
  },
});

app.use(cors());
app.use(express.json());
app.use('/api/patients', patientRoutes);
app.use('/api/patients/:id/documents', documentRoutes);
app.use('/uploads', express.static(path.join(process.cwd(), 'uploads')));

app.get('/api/health', (req, res) => {
  res.json({ status: 'ok' });
});

app.listen(port, () => {
  console.log(`🚀 Server running on http://localhost:${port}`);
});
