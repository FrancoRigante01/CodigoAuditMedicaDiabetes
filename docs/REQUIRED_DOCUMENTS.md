# Catálogo de documentación requerida para renovación

## Trámite: Renovar autorización de tratamiento para diabetes

Código del trámite: `RENOVACION_DIABETES`

### Documentos requeridos

| Requerimiento | Tipo de documento esperado | Obligatoriedad | Max. documentos | Múltiples permitidos | Advertencias permitidas |
|---|---|---|---|---|---|
| `FORMULARIO_RENOVACION` | formulario_diabetes | Obligatorio | 1 | No | Calidad |
| `ESTUDIOS_LABORATORIO` | laboratorio | Obligatorio | 2 | Sí, distintos estudios | Calidad |
| `PRESCRIPCION_MEDICA` | prescripcion | Obligatorio | 1 | No | Calidad |
| `ESTUDIO_DIAGNOSTICO` | estudio_diagnostico | Opcional | 1 | No | Calidad |

> **Nota**: `formulario_diabetes` en este contexto actúa como formulario de renovación firmado por el médico tratante. `laboratorio` puede incluir glucemia, HbA1c u otros estudios complementarios.

### Conceptos

- **Requerimiento**: un espacio documental que debe ser cubierto para que la solicitud sea válida.
- **Obligatoriedad**: si es requerido, al menos un documento válido debe estar presente.
- **Max. documentos**: cantidad máxima de documentos del mismo requerimiento.
- **Múltiples permitidos**: si se admiten varios documentos del mismo requerimiento, siempre que correspondan a estudios distintos (por ejemplo, laboratorios diferentes). En el caso de `ESTUDIOS_LABORATORIO` se permite hasta 2 documentos.
- **Advertencias permitidas**: advertencias de calidad o legibilidad no bloquean la carga ni el envío.

### Reglas de duplicados

- Un duplicado se define como un segundo documento cargado para el mismo requerimiento.
- Si el requerimiento permite múltiples documentos, los duplicados son aceptables siempre que el afiliado también los identifique como estudios distintos (por ejemplo, Glucemia y HbA1c).
- Si el requerimiento NO permite múltiples documentos, el duplicado se registra como advertencia; pero si a la vez existe algún requerimiento obligatorio sin cubrir, pasa a ser un **duplicado conflictivo** y bloquea el envío.
- Ejemplo: si el afiliado carga dos veces el `ESTUDIOS_LABORATORIO` y omite `PRESCRIPCION_MEDICA`, el sistema impedirá el envío hasta cargar la prescripción o eliminar el laboratorio duplicado.

### Umbrales de calidad

El sistema evalúa la calidad de la imagen/PDF en tres niveles:

| Dimensión | Indicador | Umbral aceptable | Acción |
|---|---|---|---|
| Resolución | Ancho x alto en píxeles | Mayor a 400x400 | Advertencia |
| Varianza de contenido | Varianza de píxeles en escala de grises | Mayor a 100 | Advertencia por imagen borrosa o en blanco |
| Confianza campos | Promedio de confianza de campos extraídos | Mayor a 40 | Advertencia de legibilidad |
| Confianza clasificación | Confianza del tipo de documento | Mayor a 50 | Advertencia por posible clasificación incorrecta |

Las advertencias no impiden continuar, pero se muestran inmediatamente al afiliado.

### Validaciones de contenido por tipo de documento

Aprovechando el validador existente:

- `formulario_diabetes`: campos requeridos, firma/datos del médico, tipo de diabetes.
- `laboratorio`: fecha del estudio, valores relevantes; varios laboratorios se tratan como instancias del mismo requerimiento.
- `prescripcion`: medicación, dosis, vigencia, matrícula del prescriptor.
- `estudio_diagnostico`: tipo de informe, fecha y conclusión.

Cuando la clasificación automática detecta un tipo distinto al requerimiento seleccionado, se agrega una advertencia informativa para que el afiliado corrija antes de enviar.
