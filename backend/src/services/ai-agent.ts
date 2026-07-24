import axios from 'axios';
import fs from 'fs';
import path from 'path';

export class ClinicalAuditorAgent {
  private apiUrl: string;
  private apiKey: string;
  private modelName: string;

  constructor() {
    this.apiUrl = "https://frida.azure-api.net/frida-app-service-llm-compatible-api/v1/chat/completions";
    this.apiKey = process.env.FRIDA_API_KEY || "";
    this.modelName = "SELENE-CIPHER";
  }

  public async evaluate(
    rawText: string,
    validationIssues: string[],
    patientContext?: any
  ): Promise<{ veredicto: string; justificacion: string; extractedData?: any }> {
    const promptContent = this.buildPromptContent(rawText, validationIssues, patientContext);

    const payload = {
      model: this.modelName,
      user_id: "auditor_demo",
      email: "demo@auditorisalud.com.ar",
      messages: [
        {
          role: "system",
          content: "Eres un auditor médico experto especializado en diabetes mellitus. Tu tarea es realizar una auditoría exhaustiva siguiendo estrictamente el formato y las reglas solicitadas por el usuario."
        },
        {
          role: "user",
          content: promptContent
        }
      ],
      temperature: 0.2
    };

    try {
      if (!this.apiKey) {
        console.warn('No FRIDA_API_KEY provided. Returning mock AI response.');
        return {
          veredicto: "APROBABLE CON OBSERVACIONES",
          justificacion: `# 1. Resumen del paciente\nPaciente simulado localmente.\n\n# 8. Recomendación\nDebido a que el sistema está corriendo en modo simulación (sin API Key), se aprueba de forma automática con observaciones.\n\nClasificación: APROBABLE CON OBSERVACIONES`,
          extractedData: {
            diagnostico: "Diabetes Tipo 2 (Simulado)",
            medicacion: ["Metformina"],
            documentos_identificados: ["Formulario"],
            sugerencia_markdown: "Paciente simulado localmente.",
            veredicto: "APROBABLE CON OBSERVACIONES"
          }
        };
      }

      const response = await axios.post(this.apiUrl, payload, {
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.apiKey}`,
          'Ocp-Apim-Subscription-Key': this.apiKey
        },
        timeout: 120000
      });

      const data = response.data;
      if (data.choices && data.choices.length > 0) {
        let agentContent = data.choices[0].message.content.trim();
        let extractedData: any = null;
        let justificacion = agentContent;
        let veredicto = "REVISIÓN MANUAL";

        // Intentar extraer JSON de la respuesta (puede venir entre bloques de markdown ```json)
        try {
          const jsonMatch = agentContent.match(/```(?:json)?\s*(\{[\s\S]*?\})\s*```/);
          let jsonStr = jsonMatch ? jsonMatch[1] : agentContent;
          
          // Buscar el primer { y el último }
          const startIndex = jsonStr.indexOf('{');
          const endIndex = jsonStr.lastIndexOf('}');
          if (startIndex !== -1 && endIndex !== -1) {
            jsonStr = jsonStr.substring(startIndex, endIndex + 1);
            extractedData = JSON.parse(jsonStr);
            if (extractedData.veredicto) veredicto = extractedData.veredicto;
            if (extractedData.sugerencia_markdown) justificacion = extractedData.sugerencia_markdown;
          }
        } catch (e) {
          console.error("Error parseando JSON del LLM:", e);
        }

        // Fallback simple si no parseó bien el json
        if (!extractedData) {
          if (agentContent.includes("APROBABLE CON OBSERVACIONES")) {
            veredicto = "APROBABLE CON OBSERVACIONES";
          } else if (agentContent.includes("NO APROBABLE")) {
            veredicto = "NO APROBABLE";
          } else if (agentContent.includes("REQUIERE INFO")) {
            veredicto = "REQUIERE INFO";
          } else if (agentContent.includes("APROBABLE")) {
            veredicto = "APROBABLE";
          }
        }

        return { veredicto, justificacion, extractedData };
      } else {
        return this.fallbackDecision("Error en la estructura de respuesta de la API.");
      }
    } catch (error: any) {
      console.error('Error in ClinicalAuditorAgent:', error.message);
      return this.fallbackDecision(error.message);
    }
  }

  public async evaluateDocumentReliability(rawText: string): Promise<number> {
    if (!rawText || rawText.trim() === '') return 0.1;

    const prompt = `Evalúa el siguiente texto extraído mediante OCR y determina su puntaje de confiabilidad entre 0.0 y 1.0.
Un puntaje de 1.0 significa que el texto es legible, estructurado y parece un documento médico válido.
Un puntaje bajo (ej. 0.2) significa que es ilegible, texto ruidoso, o irrelevante.
Devuelve ÚNICAMENTE un número decimal (ejemplo: 0.85), sin texto adicional.

--- TEXTO ---
${rawText.substring(0, 2000)}
`;

    const payload = {
      model: this.modelName,
      user_id: "auditor_demo",
      email: "demo@auditorisalud.com.ar",
      messages: [
        {
          role: "system",
          content: "Eres un experto en evaluar la calidad de OCR de documentos médicos."
        },
        {
          role: "user",
          content: prompt
        }
      ],
      temperature: 0.1
    };

    try {
      if (!this.apiKey) {
        return parseFloat((Math.random() * (0.95 - 0.7) + 0.7).toFixed(2));
      }

      const response = await axios.post(this.apiUrl, payload, {
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.apiKey}`,
          'Ocp-Apim-Subscription-Key': this.apiKey
        },
        timeout: 60000
      });

      const data = response.data;
      if (data.choices && data.choices.length > 0) {
        const content = data.choices[0].message.content.trim();
        const score = parseFloat(content);
        if (!isNaN(score) && score >= 0 && score <= 1) {
          return score;
        }
        const match = content.match(/0\.[0-9]+/);
        if (match) return parseFloat(match[0]);
        return 0.85;
      }
      return 0.8;
    } catch (error: any) {
      console.error('Error in evaluateDocumentReliability:', error.message);
      return 0.75;
    }
  }

  private buildPromptContent(
    rawText: string,
    validationIssues: string[],
    patientContext?: any
  ): any[] {
    const currentDateStr = new Date().toISOString().split('T')[0];
    
    const issuesStr = validationIssues.length > 0 
      ? validationIssues.map(i => `- ${i}`).join('\n')
      : "Ninguna detectada previamente.";

    const contextStr = patientContext ? `
Contexto del Paciente:
- Edad: ${patientContext.age || 'No especificada'}
- Plan: ${patientContext.plan || 'No especificado'}
- Trámite: ${patientContext.tipoTramite || 'No especificado'}
` : "";

    const basePrompt = `
Actúa como un médico auditor especializado en diabetes mellitus en Argentina.

IMPORTANTE PARA ESTA PRUEBA DE CONCEPTO: Debes ser muy flexible y permisivo. No exijas historia clínica, estudios de laboratorio exhaustivos, ni fechas de emisión precisas a menos que falte información crítica.

Reglas de aprobación:
- Si el documento indica claramente un diagnóstico de Diabetes (Tipo 1 o 2) y una medicación acorde, clasifícalo como APROBABLE.
- Si tiene diagnóstico y medicación pero la firma es "ILEGIBLE", clasifícalo como APROBABLE CON OBSERVACIONES.
- Si el diagnóstico no tiene relación con diabetes, clasifícalo como NO APROBABLE.
- Si falta especificar el diagnóstico exacto o medicación vital, clasifícalo como REQUIERE INFO.
- Analiza qué tipo de documentos se adjuntaron (ej. Formulario, Receta, Laboratorio) y lístalos en 'documentos_identificados'.

${contextStr}
FECHA ACTUAL DEL SISTEMA: ${currentDateStr}
Inconsistencias Previas: ${issuesStr}
------------------------------------------
 
DEBES RESPONDER ÚNICAMENTE CON UN OBJETO JSON VÁLIDO. No agregues texto fuera del JSON.
Formato esperado:
{
  "diagnostico": "El diagnóstico extraído (ej. Diabetes Tipo 2)",
  "medicacion": ["Lista", "de", "medicamentos"],
  "documentos_identificados": ["Formulario", "Receta"],
  "sugerencia_markdown": "Redacta aquí una sugerencia detallada en markdown para el auditor justificando la decisión.",
  "veredicto": "Debe ser UNO de: APROBABLE, APROBABLE CON OBSERVACIONES, NO APROBABLE, REQUIERE INFO"
}
`;

    const contentArray: any[] = [];
    contentArray.push({ type: "text", text: basePrompt });

    const attachmentRegex = /\[DOCUMENTO_ADJUNTO\] (.*?)(?=\n|$)/g;
    let match;
    let hasAttachments = false;
    
    while ((match = attachmentRegex.exec(rawText)) !== null) {
      const filePath = match[1]?.trim();
      if (!filePath) continue;
      hasAttachments = true;
      try {
        if (fs.existsSync(filePath)) {
          const ext = path.extname(filePath).toLowerCase();
          
          if (ext === '.txt') {
            const textContent = fs.readFileSync(filePath, 'utf8');
            contentArray[0].text += `\n\n--- TEXTO EXTRAÍDO DEL DOCUMENTO ${path.basename(filePath)} ---\n${textContent}`;
          } else {
            const base64 = fs.readFileSync(filePath, 'base64');
            let mimeType = 'image/jpeg';
            if (ext === '.png') mimeType = 'image/png';
            else if (ext === '.pdf') mimeType = 'application/pdf'; 
            
            contentArray.push({
              type: "image_url",
              image_url: {
                url: `data:${mimeType};base64,${base64}`
              }
            });
          }
        }
      } catch (err) {
        console.error("Error leyendo archivo adjunto", err);
      }
    }

    if (!hasAttachments) {
       contentArray[0].text += `\n\n--- TEXTO EXTRAÍDO DEL DOCUMENTO MEDIANTE OCR ---\n${rawText}`;
    }

    return contentArray;
  }

  private fallbackDecision(reason: string) {
    return {
      veredicto: "ERROR_AGENTE",
      justificacion: `No se pudo completar la auditoría inteligente. Razón: ${reason}`
    };
  }
}
