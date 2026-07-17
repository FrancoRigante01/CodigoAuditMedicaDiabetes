'''
Integration/unit tests for the renewal upload and validation flow.

Scenarios:
- complete upload -> ready for submission
- missing mandatory document -> blocks submission
- duplicate documents that cover a missing requirement -> blocks submission
- low quality document -> warning but allows submission
- submission blocked for invalid request
- classification mismatch is reported but non-blocking

WARNING: This is a DEMO with FICTIONAL DATA ONLY.
'''

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import tempfile

from PIL import Image

from src.renewal_models import SolicitudStatus
from src.renewal_upload_service import RenewalUploadService
from src.renewal_validation_service import RenewalValidationService


def _create_dummy_image(path, size=(800, 800)):
    '''Create a simple RGB image for testing.'''

    img = Image.new('RGB', size, color=(255, 255, 255))
    img.save(path)


def _dummy_file_storage(path):
    '''Wrap a file path in a FileStorage-like object for the upload service.'''

    from werkzeug.datastructures import FileStorage
    f = Path(path).open('rb')
    return FileStorage(stream=f, filename=path.name)


def test_missing_mandatory_blocks_submission():
    service = RenewalUploadService(base_storage_path=tempfile.mkdtemp(prefix='renewal_'))
    solicitud = service.create_solicitud()
    validator = RenewalValidationService()
    result = validator.process_and_validate(solicitud)

    assert result.can_submit is False
    assert result.status == SolicitudStatus.DOCS_INCOMPLETAS
    assert len(result.issues) >= 4
    issue_types = {i.issue_type for i in result.issues}
    assert 'missing' in issue_types
    print('OK missing mandatory document blocks submission')


def test_complete_upload_allows_submission():
    base = tempfile.mkdtemp(prefix='renewal_')
    service = RenewalUploadService(base_storage_path=base)
    solicitud = service.create_solicitud()
    validator = RenewalValidationService()

    requirements = {
        'FORMULARIO_RENOVACION': 'formulario_diabetes',
        'ESTUDIOS_LABORATORIO': 'laboratorio',
        'PRESCRIPCION_MEDICA': 'prescripcion',
        'ESTUDIO_DIAGNOSTICO': 'estudio_diagnostico',
    }

    for req_id, doc_name in requirements.items():
        doc_path = Path(base) / (doc_name + '.png')
        _create_dummy_image(doc_path)
        from PIL import ImageDraw, ImageFont
        try:
            font = ImageFont.truetype('arial.ttf', 36)
        except Exception:
            font = ImageFont.load_default()
        img = Image.open(doc_path)
        draw = ImageDraw.Draw(img)
        draw.text((20, 20), doc_name.replace('_', ' '), fill=(0, 0, 0), font=font)
        img.save(doc_path)

        storage = _dummy_file_storage(doc_path)
        service.store_document(solicitud, req_id, storage)

    result = validator.process_and_validate(solicitud)
    assert result.can_submit is True, 'Expected ready to submit, got: ' + str(result.messages)
    assert result.status == SolicitudStatus.LISTA_PARA_ENVIO
    print('OK complete upload allows submission')


def test_duplicate_study_blocks_submission():
    base = tempfile.mkdtemp(prefix='renewal_')
    service = RenewalUploadService(base_storage_path=base)
    solicitud = service.create_solicitud()
    validator = RenewalValidationService()

    # Upload more than max_documents identical lab reports to force duplicate detection.
    for i in range(6):
        doc_path = Path(base) / f'laboratorio_{i}.png'
        _create_dummy_image(doc_path)
        from PIL import ImageDraw
        img = Image.open(doc_path)
        draw = ImageDraw.Draw(img)
        draw.text((20, 20), 'laboratorio glucosa', fill=(0, 0, 0))
        img.save(doc_path)
        storage = _dummy_file_storage(doc_path)
        service.store_document(solicitud, 'ESTUDIOS_LABORATORIO', storage)

    result = validator.process_and_validate(solicitud)
    assert result.can_submit is False
    assert result.status == SolicitudStatus.DOCS_INCOMPLETAS
    assert any(i.issue_type == 'duplicate' for i in result.issues)
    print('OK duplicate study is flagged')


def test_quality_warning_allows_submission():
    base = tempfile.mkdtemp(prefix='renewal_')
    service = RenewalUploadService(base_storage_path=base)
    solicitud = service.create_solicitud()
    validator = RenewalValidationService()

    requirements = {
        'FORMULARIO_RENOVACION': 'formulario_diabetes',
        'ESTUDIOS_LABORATORIO': 'laboratorio',
        'PRESCRIPCION_MEDICA': 'prescripcion',
        'ESTUDIO_DIAGNOSTICO': 'estudio_diagnostico',
    }

    for idx, (req_id, doc_name) in enumerate(requirements.items()):
        doc_path = Path(base) / (doc_name + '_' + str(idx) + '.png')
        size = (200, 200) if idx == 0 else (800, 800)
        _create_dummy_image(doc_path, size=size)
        from PIL import ImageDraw
        img = Image.open(doc_path)
        draw = ImageDraw.Draw(img)
        draw.text((10, 10), doc_name.replace('_', ' '), fill=(0, 0, 0))
        img.save(doc_path)
        storage = _dummy_file_storage(doc_path)
        service.store_document(solicitud, req_id, storage)

    # Force the first document to have no processing result so quality fallback is used.
    solicitud.documents[0].processing_result = None
    result = validator.validate(solicitud)
    assert result.can_submit is True, 'Expected submit allowed, got: ' + str(result.messages)
    assert any(i.issue_type == 'quality' for i in result.issues)
    print('OK quality warning allows submission')


def test_submission_service_blocks_invalid_request():
    base = tempfile.mkdtemp(prefix='renewal_')
    service = RenewalUploadService(base_storage_path=base)
    solicitud = service.create_solicitud()
    validator = RenewalValidationService()
    result = validator.process_and_validate(solicitud)

    assert result.can_submit is False
    try:
        service.mark_submitted(solicitud, result)
    except ValueError as exc:
        assert 'No se puede enviar la solicitud' in str(exc)
        print('OK submission service blocks invalid request')
        return
    raise AssertionError('Expected ValueError for invalid submission')


def test_classification_mismatch_is_non_blocking_warning():
    base = tempfile.mkdtemp(prefix='renewal_')
    service = RenewalUploadService(base_storage_path=base)
    solicitud = service.create_solicitud()
    validator = RenewalValidationService()

    # Upload a lab document under the prescription requirement to force a mismatch.
    doc_path = Path(base) / 'laboratorio.png'
    _create_dummy_image(doc_path)
    from PIL import ImageDraw
    img = Image.open(doc_path)
    draw = ImageDraw.Draw(img)
    draw.text((20, 20), 'glucemia', fill=(0, 0, 0))
    img.save(doc_path)

    storage = _dummy_file_storage(doc_path)
    service.store_document(solicitud, 'PRESCRIPCION_MEDICA', storage)

    result = validator.process_and_validate(solicitud)
    classification_issues = [i for i in result.issues if i.issue_type == 'classification']
    assert len(classification_issues) >= 1
    assert not any(i.blocks_submission for i in classification_issues)
    # Missing the remaining mandatory requirements should still block submission.
    assert result.can_submit is False
    assert result.status == SolicitudStatus.DOCS_INCOMPLETAS
    print('OK classification mismatch is warning but missing docs block submission')


def test_conflicting_duplicate_blocks_submission():
    base = tempfile.mkdtemp(prefix='renewal_')
    service = RenewalUploadService(base_storage_path=base)
    solicitud = service.create_solicitud()
    validator = RenewalValidationService()

    # Upload two identical lab documents but assigned to different requirements,
    # leaving one mandatory requirement empty.
    for idx, req_id in enumerate(['ESTUDIOS_LABORATORIO', 'ESTUDIO_DIAGNOSTICO']):
        doc_path = Path(base) / f'laboratorio_conflict_{idx}.png'
        _create_dummy_image(doc_path)
        from PIL import ImageDraw
        img = Image.open(doc_path)
        draw = ImageDraw.Draw(img)
        draw.text((20, 20), 'laboratorio glucosa', fill=(0, 0, 0))
        img.save(doc_path)
        storage = _dummy_file_storage(doc_path)
        service.store_document(solicitud, req_id, storage)

    result = validator.process_and_validate(solicitud)
    assert result.can_submit is False
    assert any(i.issue_type in {'missing', 'conflicting_duplicate'} for i in result.issues)
    print('OK conflicting duplicate blocks submission')


def run_all_tests():
    print('\n' + '=' * 70)
    print('RENEWAL VALIDATION FLOW TESTS')
    print('=' * 70 + '\n')
    test_missing_mandatory_blocks_submission()
    test_complete_upload_allows_submission()
    test_duplicate_study_blocks_submission()
    test_quality_warning_allows_submission()
    test_submission_service_blocks_invalid_request()
    test_classification_mismatch_is_non_blocking_warning()
    test_conflicting_duplicate_blocks_submission()
    print('\n' + '=' * 70)
    print('ALL RENEWAL TESTS PASSED')
    print('=' * 70 + '\n')


if __name__ == '__main__':
    run_all_tests()

