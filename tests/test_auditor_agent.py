import unittest
from unittest.mock import patch, MagicMock
from src.auditor_agent import ClinicalAuditorAgent
from src.models import ExtractedField

class TestClinicalAuditorAgent(unittest.TestCase):
    def setUp(self):
        self.agent = ClinicalAuditorAgent()
        self.dummy_fields = {
            "diagnostico": ExtractedField(valor="Diabetes Tipo 2", confianza=100)
        }

    @patch("src.auditor_agent.requests.post")
    def test_aprobacion_completa(self, mock_post):
        # Configurar el mock para devolver APROBABLE
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": "Revisión completada.\n\n# 8. Recomendación\nAPROBABLE\n\nTodo correcto."
                }
            }]
        }
        mock_post.return_value = mock_response

        resultado = self.agent.evaluate("formulario_diabetes", self.dummy_fields, [])
        self.assertEqual(resultado["veredicto"], "APROBABLE")

    @patch("src.auditor_agent.requests.post")
    def test_aprobacion_parcial(self, mock_post):
        # Configurar el mock para devolver APROBABLE CON OBSERVACIONES
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": "Revisión completada.\n\n# 8. Recomendación\nAPROBABLE CON OBSERVACIONES\n\nFalta firma en un documento menor."
                }
            }]
        }
        mock_post.return_value = mock_response

        resultado = self.agent.evaluate("formulario_diabetes", self.dummy_fields, ["Firma poco clara"])
        self.assertEqual(resultado["veredicto"], "APROBABLE CON OBSERVACIONES")

    @patch("src.auditor_agent.requests.post")
    def test_rechazo(self, mock_post):
        # Configurar el mock para devolver NO APROBABLE
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": "Revisión completada.\n\n# 8. Recomendación\nNO APROBABLE\n\nNo cumple con criterios básicos."
                }
            }]
        }
        mock_post.return_value = mock_response

        resultado = self.agent.evaluate("formulario_diabetes", self.dummy_fields, ["Falta historia clínica"])
        self.assertEqual(resultado["veredicto"], "NO APROBABLE")

    @patch("src.auditor_agent.requests.post")
    def test_solicitar_informacion(self, mock_post):
        # Configurar el mock para devolver REVISIÓN MANUAL (o REQUIERE INFO)
        # El agente actualmente usa REVISIÓN MANUAL si no encuentra APROBABLE, APROBABLE CON OBSERVACIONES o NO APROBABLE
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": "Revisión completada.\n\n# 8. Recomendación\nSOLICITAR INFORMACION\n\nFalta aclarar dosis."
                }
            }]
        }
        mock_post.return_value = mock_response

        resultado = self.agent.evaluate("formulario_diabetes", self.dummy_fields, ["Dosis no especificada"])
        # Como "SOLICITAR INFORMACION" no está en los if del código base de ClinicalAuditorAgent,
        # va a caer en el fallback del veredicto: "REVISIÓN MANUAL"
        self.assertEqual(resultado["veredicto"], "REVISIÓN MANUAL")

if __name__ == "__main__":
    unittest.main()
