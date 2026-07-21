import logging
import json
import requests
from typing import Dict, Any, List
from .models import ExtractedField

logger = logging.getLogger(__name__)

class ClinicalAuditorAgent:
    """
    Agente de IA que interactúa con la API de FRIDA (Kimi 2.7 Code) 
    para tomar decisiones de auditoría clínica basadas en los datos extraídos 
    y las validaciones previas.
    """

    def __init__(self):
        import os
        # Configuración de la API de FRIDA
        self.api_url = "https://frida.azure-api.net/frida-app-service-llm-compatible-api/v1/chat/completions"
        self.api_key = os.environ.get("FRIDA_API_KEY", "")
        self.model_name = "SELENE-CIPHER"

    def evaluate(
        self,
        document_type: str,
        extracted_fields: Dict[str, ExtractedField],
        validation_issues: List[str]
    ) -> Dict[str, Any]:
        """
        Evalúa los datos extraídos y las validaciones previas para emitir un veredicto.
        """
        prompt = self._build_prompt(document_type, extracted_fields, validation_issues)
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "Ocp-Apim-Subscription-Key": self.api_key
        }

        payload = {
            "model": self.model_name,
            "user_id": "auditor_demo",
            "email": "demo@sancorsalud.com.ar",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Eres un auditor médico experto de Sancor Salud encargado de auditar documentación para pacientes con diabetes. "
                        "Recibirás datos extraídos de un documento y posibles inconsistencias previas. "
                        "Debes responder ÚNICAMENTE con un JSON válido, sin formato markdown, con la siguiente estructura exacta: "
                        '{"veredicto": "APROBADO" | "RECHAZADO" | "REQUIERE_INFO", "justificacion": "Explicación detallada de la decisión clínica."}'
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.2
        }

        try:
            logger.info("Enviando solicitud a FRIDA API para auditoría clínica...")
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
            
            # Comprobar si el request fue exitoso
            if not response.ok:
                logger.error(f"FRIDA API Error {response.status_code}: {response.text}")
            response.raise_for_status()
            
            response_json = response.json()
            
            if "choices" in response_json and len(response_json["choices"]) > 0:
                agent_content = response_json["choices"][0]["message"]["content"]
                
                # Intentar parsear el JSON de la respuesta
                agent_content = agent_content.strip()
                if agent_content.startswith("```json"):
                    agent_content = agent_content[7:]
                if agent_content.endswith("```"):
                    agent_content = agent_content[:-3]
                
                decision = json.loads(agent_content.strip())
                return decision
            else:
                logger.error(f"Respuesta inesperada de FRIDA API: {response_json}")
                return self._fallback_decision("Error en la estructura de respuesta de la API.")
                
        except requests.exceptions.RequestException as e:
            error_details = getattr(e.response, 'text', str(e))
            logger.error(f"Error de conexión con FRIDA API: {e} - Details: {error_details}")
            return self._fallback_decision(f"Error 400. Detalles de la API: {error_details}")
        except json.JSONDecodeError as e:
            logger.error(f"Error parseando la respuesta del Agente: {e} - Content: {agent_content}")
            return self._fallback_decision("El Agente no respondió con un JSON válido.")
        except Exception as e:
            logger.error(f"Error desconocido en ClinicalAuditorAgent: {e}")
            return self._fallback_decision(str(e))

    def _build_prompt(
        self,
        document_type: str,
        extracted_fields: Dict[str, ExtractedField],
        validation_issues: List[str]
    ) -> str:
        """
        Construye el prompt detallado para el Agente Auditor Clínico.
        """
        import datetime
        current_date_str = datetime.datetime.now().strftime("%Y-%m-%d")
        
        fields_str = "\n".join([f"- {k}: {v.valor} (Confianza: {v.confianza}%)" for k, v in extracted_fields.items()])
        issues_str = "\n".join([f"- {i}" for i in validation_issues]) if validation_issues else "Ninguna detectada previamente."

        return f"""
Eres un Auditor Médico Experto especializado en evaluación de solicitudes de medicación e insumos, en particular para Diabetes.
Tu objetivo es tomar la información extraída automáticamente de un documento médico y decidir si se debe APROBAR, RECHAZAR, o si REQUIERE_INFO adicional.

FECHA ACTUAL DEL SISTEMA: {current_date_str} (Usa esta fecha para validar la antigüedad o vigencia de los documentos).

Tipo de Documento: {document_type}

Campos Extraídos:
{fields_str}

Inconsistencias Detectadas por Validación Inicial:
{issues_str}

Reglas de Auditoría:
1. Si faltan datos críticos o hay inconsistencias clínicas graves, el veredicto debe ser "RECHAZADO" o "REQUIERE_INFO".
2. Si el documento parece completo, los datos son coherentes clínicamente y no hay alertas críticas, el veredicto es "APROBADO".
3. Proporciona una justificación médica o administrativa clara para la decisión.
"""

    def _fallback_decision(self, reason: str) -> Dict[str, Any]:
        """Devuelve una decisión por defecto en caso de fallo del agente."""
        return {
            "veredicto": "ERROR_AGENTE",
            "justificacion": f"No se pudo completar la auditoría inteligente. Razón: {reason}"
        }
