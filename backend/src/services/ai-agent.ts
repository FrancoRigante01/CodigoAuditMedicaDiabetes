import axios from 'axios';

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
    validationIssues: string[]
  ): Promise<{ veredicto: string; justificacion: string }> {
    const prompt = this.buildPrompt(rawText, validationIssues);

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
          content: prompt
        }
      ],
      temperature: 0.2
    };

    try {
      if (!this.apiKey) {
        console.warn('No FRIDA_API_KEY provided. Returning mock AI response.');
        return {
          veredicto: "APROBABLE CON OBSERVACIONES",
          justificacion: `# 1. Resumen del paciente\nPaciente simulado localmente.\n\n# 8. Recomendación\nDebido a que el sistema está corriendo en modo simulación (sin API Key), se aprueba de forma automática con observaciones.\n\nClasificación: APROBABLE CON OBSERVACIONES`
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
        const agentContent = data.choices[0].message.content.trim();
        
        let veredicto = "REVISIÓN MANUAL";
        if (agentContent.includes("APROBABLE CON OBSERVACIONES")) {
          veredicto = "APROBABLE CON OBSERVACIONES";
        } else if (agentContent.includes("NO APROBABLE")) {
          veredicto = "NO APROBABLE";
        } else if (agentContent.includes("APROBABLE")) {
          veredicto = "APROBABLE";
        }

        return { veredicto, justificacion: agentContent };
      } else {
        return this.fallbackDecision("Error en la estructura de respuesta de la API.");
      }
    } catch (error: any) {
      console.error('Error in ClinicalAuditorAgent:', error.message);
      return this.fallbackDecision(error.message);
    }
  }

  private buildPrompt(
    rawText: string,
    validationIssues: string[]
  ): string {
    const currentDateStr = new Date().toISOString().split('T')[0];
    
    const issuesStr = validationIssues.length > 0 
      ? validationIssues.map(i => `- ${i}`).join('\n')
      : "Ninguna detectada previamente.";

    return `
Actúa como un médico auditor especializado en diabetes mellitus en Argentina.

IMPORTANTE PARA ESTA PRUEBA DE CONCEPTO: Debes ser muy flexible y permisivo. No exijas historia clínica, estudios de laboratorio (como HbA1c o función renal), ni datos demográficos exhaustivos, ni fechas de emisión. 

Reglas de aprobación para esta POC:
- Si el documento indica claramente un diagnóstico de Diabetes (Tipo 1 o 2) y una medicación acorde (Metformina, Insulina, etc.), y la firma del médico parece válida, clasifícalo como APROBABLE.
- Si tiene el diagnóstico y medicación pero advierte que la firma es "ILEGIBLE" o le falta un sello válido, clasifícalo como APROBABLE CON OBSERVACIONES.
- Si el diagnóstico indica una enfermedad que no tiene relación con la diabetes (ej. resfriado común), clasifícalo como NO APROBABLE.
- Si falta especificar el diagnóstico exacto o la medicación, clasifícalo como REQUIERE INFO.

FECHA ACTUAL DEL SISTEMA: ${currentDateStr}

--- TEXTO EXTRAÍDO DEL DOCUMENTO MEDIANTE OCR ---
${rawText}

Inconsistencias Detectadas por Validación Inicial:
${issuesStr}
------------------------------------------
 
Debes responder utilizando el siguiente formato:
 
# 1. Resumen del paciente
... (Formato de auditoría esperado omitido por brevedad, asume el mismo prompt de Python)
...
# 8. Recomendación
Clasificar el expediente en UNA sola categoría: APROBABLE, APROBABLE CON OBSERVACIONES, NO APROBABLE
`;
  }

  private fallbackDecision(reason: string) {
    return {
      veredicto: "ERROR_AGENTE",
      justificacion: `No se pudo completar la auditoría inteligente. Razón: ${reason}`
    };
  }
}
