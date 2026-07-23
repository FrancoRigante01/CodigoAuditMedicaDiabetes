import { ClinicalAuditorAgent } from './ai-agent';
import fs from 'fs';
import path from 'path';
import Tesseract from 'tesseract.js';
const pdfParse = require('pdf-parse');

export class MedicalDocumentProcessor {
  private agent: ClinicalAuditorAgent;

  constructor() {
    this.agent = new ClinicalAuditorAgent();
  }

  public async extractTextFromFile(filePath: string): Promise<string> {
    const ext = path.extname(filePath).toLowerCase();
    try {
      if (ext === '.pdf') {
        const dataBuffer = fs.readFileSync(filePath);
        const data = await pdfParse(dataBuffer);
        return data.text;
      } else if (ext === '.png' || ext === '.jpg' || ext === '.jpeg') {
        // Usar español 'spa' asumiendo documentos en Argentina
        const { data: { text } } = await Tesseract.recognize(filePath, 'spa');
        return text;
      } else {
        throw new Error('Formato de archivo no soportado. Debe ser PDF, PNG o JPG.');
      }
    } catch (error) {
      console.error('Error extrayendo texto:', error);
      throw new Error('Fallo al extraer texto del documento.');
    }
  }

  public async processDocument(filename: string, filePath: string) {
    const rawText = await this.extractTextFromFile(filePath);
    
    const docType = "Documento Médico";

    // Agent evaluation
    const agentDecision = await this.agent.evaluate(rawText, []);

    return {
      tipo_documento: docType,
      confianza_clasificacion: 90,
      veredicto_auditoria: agentDecision.veredicto,
      justificacion_auditoria: agentDecision.justificacion,
      faltantes_o_inconsistencias: []
    };
  }
  public async evaluateMultipleDocuments(texts: string[]) {
    const combinedText = texts.join('\n\n--- SIGUIENTE DOCUMENTO ---\n\n');
    
    // Agent evaluation
    const agentDecision = await this.agent.evaluate(combinedText, []);

    return {
      confianza_clasificacion: 90,
      veredicto_auditoria: agentDecision.veredicto,
      justificacion_auditoria: agentDecision.justificacion,
      faltantes_o_inconsistencias: []
    };
  }

  public async evaluateReliability(rawText: string): Promise<number> {
    return await this.agent.evaluateDocumentReliability(rawText);
  }
}
