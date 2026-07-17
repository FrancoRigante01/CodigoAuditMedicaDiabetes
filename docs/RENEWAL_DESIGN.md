# Diseño funcional: Carga y validación de documentación para renovación

## Alcance

El afiliado debe poder cargar la documentación requerida para solicitar una renovación de autorización de diabetes. Durante la carga, el sistema ejecutará validaciones automáticas y le informará de forma inmediata si detecta:

- Documentación faltante.
- Documentación duplicada que cubre el mismo requerimiento.
- Problemas de calidad de imagen o legibilidad.
- Tipo de documento cargado, aprovechando el clasificador existente.

## Actores

- **Afiliado**: carga documentos y decide cuándo enviar la solicitud.
- **Sistema**: recibe, almacena, clasifica, valida e informa.
- **Auditoría**: recibe únicamente solicitudes completas y válidas.

## Estados de una solicitud de renovación

| Estado | Descripción |
|---|---|
| `BORRADOR` | Solicitud creada, aún sin documentos cargados. |
| `DOCS_EN_CARGA` | Existen documentos cargados, aún no se intenta enviar. |
| `DOCS_INCOMPLETAS` | Falta documentación obligatoria o existen duplicados conflictivos. |
| `DOCS_WARNING_CALIDAD` | Documentación completa con advertencias de calidad/legibilidad. |
| `LISTA_PARA_ENVIO` | Documentación completa, sin conflictos. |
| `EN_AUDITORIA` | Solicitud enviada y disponible para auditoría. |

## Flujo de carga y validación

1. El afiliado inicia una renovación; el sistema crea una solicitud en estado `BORRADOR` y expone el catálogo de documentos requeridos.
2. Por cada documento, el afiliado selecciona un tipo/requerimiento y sube el archivo.
3. El backend recibe el archivo, lo almacena de forma segura y ejecuta:
   - Detección de calidad de imagen.
   - Lectura y extracción de texto/imágenes.
   - Clasificación automática con el módulo actual.
   - Validación de campos del documento.
4. El backend registra el documento en la solicitud con su tipo detectado, confianza y alertas.
5. El sistema recalcula el estado global de la solicitud y envía notificación inmediata con:
   - Requerimientos faltantes.
   - Duplicados detectados.
   - Advertencias de calidad.
   - Permitividad de continuar con advertencias.
6. El afiliado puede seguir cargando documentos aunque existan advertencias de calidad.
7. Al presionar “Enviar solicitud”, el sistema verifica:
   - No faltar documentación obligatoria.
   - No existir duplicados conflictivos (dos documentos del mismo requerimiento mientras otro requerimiento obligatorio está sin cubrir).
8. Si todo es válido, la solicitud pasa a `LISTA_PARA_ENVIO` y luego a `EN_AUDITORIA`.
9. Si hay bloqueos, se impide el envío y se muestran las acciones correctivas.

## Decisiones del usuario

- ** Continuar con advertencias de calidad**: permitido.
- **Enviar con documentación obligatoria faltante**: bloqueado.
- **Enviar con duplicados conflictivos**: bloqueado.
- **Eliminar o reemplazar un documento**: permitido mientras la solicitud no haya sido enviada.

## Reglas de negocio críticas

| Regla | Impacto |
|---|---|
| Todo requerimiento marcado como obligatorio debe tener al menos un documento válido al enviar. | Bloquea envío. |
| Un documento duplicado del mismo requerimiento no genera problema si todos los requerimientos obligatorios están cubiertos. | Solo advertencia. |
| Si existe un duplicado y otro requerimiento obligatorio no está cubierto, el duplicado se considera conflictivo. | Bloquea envío hasta que se complete el requerimiento faltante o se corrija el duplicado. |
| Advertencias de calidad o legibilidad no impiden continuar cargando ni enviar. | Advertencia, no bloqueo. |
| La clasificación automática puede advertir si el tipo detectado difiere del requerimiento seleccionado. | Advertencia informativa. |
| Las solicitudes incompletas o inválidas nunca avanzan a la instancia de auditoría. | Filtro de integridad. |

## Notificación inmediata

El sistema responde a cada carga y al intento de envío con un objeto JSON que incluye:

- `can_submit`: booleano.
- `status`: estado calculado de la solicitud.
- `missing_requirements`: lista de requerimientos obligatorios sin cubrir.
- `duplicate_issues`: lista de duplicados detectados.
- `conflicting_duplicates`: duplicados que impiden enviar.
- `quality_warnings`: advertencias de calidad de imagen o legibilidad.
- `messages`: mensajes legibles para el afiliado.

La interfaz mostrará esos mensajes de forma inline por categoría: error (rojo), advertencia (amarillo) e información (azul).

## Integración con auditoría

Solo las solicitudes en estado `LISTA_PARA_ENVIO` o `EN_AUDITORIA` serán expuestas al flujo de auditoría. El módulo de auditoría consultará un filtro que descarte cualquier solicitud en estados `DOCS_INCOMPLETAS` o `BORRADOR`.
