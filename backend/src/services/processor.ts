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
  public async evaluateMultipleDocuments(texts: string[], patientContext?: any) {
    const combinedText = texts.join('\n\n--- SIGUIENTE DOCUMENTO ---\n\n');
    
    // Agent evaluation
    const agentDecision = await this.agent.evaluate(combinedText, [], patientContext);

    // Validation logic for missing docs
    let finalVerdict = agentDecision.veredicto;
    let finalJustificacion = agentDecision.justificacion;

    if (patientContext && agentDecision.extractedData) {
      const docs = agentDecision.extractedData.documentos_identificados || [];
      const hasForm = docs.some((d: string) => d.toLowerCase().includes('form'));
      const hasReceta = docs.some((d: string) => d.toLowerCase().includes('receta'));
      
      if (patientContext.tipoTramite === 'Empadronamiento Inicial') {
        if (!hasForm || !hasReceta) {
          finalVerdict = 'REQUIERE INFO';
          finalJustificacion = `> [!WARNING]\n> Faltan documentos obligatorios para el Empadronamiento Inicial (Formulario y/o Receta).\n\n` + finalJustificacion;
          agentDecision.extractedData.veredicto = finalVerdict;
        }
      }
    }

    return {
      confianza_clasificacion: 90,
      veredicto_auditoria: finalVerdict,
      justificacion_auditoria: finalJustificacion,
      faltantes_o_inconsistencias: [],
      extractedData: agentDecision.extractedData
    };
  }

  public async evaluateReliability(rawText: string): Promise<number> {
    if (rawText.includes('[DOCUMENTO_ADJUNTO]')) return 1.0; // Si es un adjunto directo, asumimos máxima confiabilidad inicial
    return await this.agent.evaluateDocumentReliability(rawText);
  }
}
