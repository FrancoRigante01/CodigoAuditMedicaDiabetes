'''
Integration tests for the renewal API and audit-flow gatekeeper.

Scenarios:
- API blocks submission for incomplete renewal requests (HTTP 422)
- API allows submission for complete, valid renewal requests -> EN_AUDITORIA
- Invalid requests never reach the auditing instance

WARNING: This is a DEMO with FICTIONAL DATA ONLY.
'''

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import tempfile

from PIL import Image

from web_app import app


def _create_dummy_image(path, size=(800, 800), text='demo'):
    '''Create a simple RGB image for testing.'''

    img = Image.new('RGB', size, color=(255, 255, 255))
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    draw.text((20, 20), text, fill=(0, 0, 0))
    img.save(path)


def _client():
    '''Return a Flask test client with app context.'''

    app.config['RENEWAL_UPLOAD_PATH'] = tempfile.mkdtemp(prefix='renewal_api_')
    app.config['TESTING'] = True
    return app.test_client()


def test_create_solicitud():
    client = _client()
    resp = client.post('/api/renovacion/solicitudes', json={'affiliate_id': 'A123'})
    assert resp.status_code == 201
    data = resp.get_json()
    assert data['solicitud_model']['status'] == 'BORRADOR'
    print('OK create solicitud via API')


def test_invalid_request_blocked_from_audit():
    client = _client()
    resp = client.post('/api/renovacion/solicitudes', json={'affiliate_id': 'A123'})
    solicitud_id = resp.get_json()['solicitud_model']['solicitud_id']

    submit_resp = client.post(f'/api/renovacion/solicitudes/{solicitud_id}/enviar')
    assert submit_resp.status_code == 422
    data = submit_resp.get_json()
    assert data['success'] is False
    assert data['validation']['can_submit'] is False
    assert data['validation']['status'] == 'DOCS_INCOMPLETAS'
    print('OK invalid request is blocked from audit (HTTP 422)')


def test_valid_request_reaches_audit():
    client = _client()
    resp = client.post('/api/renovacion/solicitudes', json={'affiliate_id': 'A123'})
    solicitud_id = resp.get_json()['solicitud_model']['solicitud_id']

    base = Path(app.config['RENEWAL_UPLOAD_PATH'])
    requirements = {
        'FORMULARIO_RENOVACION': 'formulario_diabetes',
        'ESTUDIOS_LABORATORIO': 'laboratorio',
        'PRESCRIPCION_MEDICA': 'prescripcion',
        'ESTUDIO_DIAGNOSTICO': 'estudio_diagnostico',
    }

    for req_id, doc_name in requirements.items():
        doc_path = base / f'{doc_name}.png'
        _create_dummy_image(doc_path, text=doc_name.replace('_', ' '))
        with doc_path.open('rb') as f:
            upload_resp = client.post(
                f'/api/renovacion/solicitudes/{solicitud_id}/documentos',
                data={
                    'document': (f, f'{doc_name}.png'),
                    'requirement_id': req_id,
                },
                content_type='multipart/form-data',
            )
        assert upload_resp.status_code == 200, upload_resp.get_json()

    validate_resp = client.get(f'/api/renovacion/solicitudes/{solicitud_id}/validar')
    validation = validate_resp.get_json()
    assert validation['can_submit'] is True, validation['messages']
    assert validation['status'] == 'LISTA_PARA_ENVIO'

    submit_resp = client.post(f'/api/renovacion/solicitudes/{solicitud_id}/enviar')
    assert submit_resp.status_code == 200
    submit_data = submit_resp.get_json()
    assert submit_data['success'] is True
    assert submit_data['validation']['can_submit'] is True

    # Verify the in-memory solicitud state reflects EN_AUDITORIA. The validation
    # result returned by /validar is recomputed from the documents and therefore
    # still reports LISTA_PARA_ENVIO; the important gatekeeper is the request status.
    from src.renewal_api import SOLICITUDES
    assert SOLICITUDES[solicitud_id].status.value == 'EN_AUDITORIA'
    print('OK valid request reaches audit after passing validation')


def test_catalog_endpoint():
    client = _client()
    resp = client.get('/api/renovacion/catalogo/RENOVACION_DIABETES')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['procedure_code'] == 'RENOVACION_DIABETES'
    req_ids = {r['requirement_id'] for r in data['requirements']}
    assert 'FORMULARIO_RENOVACION' in req_ids
    assert 'ESTUDIOS_LABORATORIO' in req_ids
    print('OK catalog endpoint returns renewal requirements')


def run_all_tests():
    print('\n' + '=' * 70)
    print('RENEWAL API INTEGRATION TESTS')
    print('=' * 70 + '\n')
    test_create_solicitud()
    test_invalid_request_blocked_from_audit()
    test_valid_request_reaches_audit()
    test_catalog_endpoint()
    print('\n' + '=' * 70)
    print('ALL RENEWAL API INTEGRATION TESTS PASSED')
    print('=' * 70 + '\n')


if __name__ == '__main__':
    run_all_tests()
