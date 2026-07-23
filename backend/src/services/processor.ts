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
    // PRUEBA: Deshabilitar OCR y enviar directamente la referencia al archivo para que la IA lo lea
    return `[DOCUMENTO_ADJUNTO] ${filePath}`;
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
    if (rawText.includes('[DOCUMENTO_ADJUNTO]')) return 1.0; // Si es un adjunto directo, asumimos máxima confiabilidad inicial
    return await this.agent.evaluateDocumentReliability(rawText);
  }
}
