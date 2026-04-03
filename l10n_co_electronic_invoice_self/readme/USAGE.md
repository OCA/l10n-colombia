## Requisitos

- Módulo `l10n_co_electronic_invoice` instalado.
- Módulo `certificate` nativo de Odoo (habilitación y producción).
- Python: `xmlsig`, `lxml`, `cryptography`, `xmltodict`, `requests`, `qrcode`.

## Configuración del diario

**Contabilidad > Configuración > Diarios** → pestaña DIAN:

- **Modo de Operación**: Demostración, Habilitación o Producción.
- **Software ID y PIN**: asignados por la DIAN al registrar el software.
- **TestSetId** (solo habilitación): UUID del set de pruebas.

**Habilitación/Demostración** — configurar manualmente:

- Tipo de resolución, resolución, prefijo, rango, clave técnica.

**Producción** — botón "Obtener resolución DIAN":

- Configurar resolución y prefijo antes de consultar.
- Llena automáticamente rango, fechas y clave técnica.
- Si hay múltiples prefijos con la misma resolución, el match
  usa resolución + prefijo.

## Configuración de empresa

- NIT con dígito de verificación (ej: `000000000-0`).
- Régimen fiscal (IVA / No responsable).
- Responsabilidades fiscales.
- Código CIIU.

## Configuración de clientes

**Nacionales**: país Colombia, NIT/CC, tipo de identificación,
régimen fiscal, responsabilidades fiscales.

**Extranjeros**: país, nombre, tipo de identificación
(ID Extranjera o NIT otro país), número de identificación.

**Consumidor final**: se asigna tipo `13` (CC) automáticamente
si no tiene tipo configurado.

## Configuración de impuestos

Cada impuesto debe tener el campo **Tipo de impuesto DIAN**
(`l10n_co_tax_type_id`) configurado con el código correcto:
`01` (IVA), `03` (ICA), `04` (INC), `05` (ReteIVA), etc.

## Configuración de productos

- Código UNSPSC o referencia interna.
- Impuesto y unidad de medida con código UNECE.
- Para exportación (tipo 02): marca y modelo obligatorios.

## Certificado digital

Cargar en **Ajustes > Certificados** (`.pem` + clave privada).
En demostración se usa certificado demo incluido.

## Flujo de facturación

1. Crear y confirmar la factura.
2. El CRON EDI genera el XML, firma y envía a DIAN.
3. Resultado en el chatter (aceptado, rechazado, error).
4. Si aceptado: se genera AttachedDocument.

### Habilitación (asíncrono)

- `SendTestSetAsync` retorna ZipKey → estado "Enviado".
- Botón **Consultar Estado DIAN** ejecuta `GetStatusZip`.
- Si aceptado: genera AttachedDocument.

### Producción (sincrónico)

- `SendBillSync` retorna resultado inmediato.
- Botón **Consultar Estado DIAN** ejecuta `GetStatus` por CUFE.

## Factura de exportación (tipo 02)

- Moneda: USD en Odoo, pero el XML va en COP con TRM.
- Cliente con país distinto de Colombia.
- Productos con marca y modelo configurados.
- `CustomizationID = "32"` automático.
- `PaymentExchangeRate` con TRM (COP/USD).

## Notas crédito y débito

- **Con referencia**: desde botón en la factura. Requiere CUFE
  y estado aceptado en la factura original.
- **Sin referencia**: crear manualmente. Requiere periodo de
  facturación (fecha inicio y fin).
- Concepto de corrección obligatorio (tabla DIAN 13.2.4/13.2.5).

## Importación de facturas de proveedor

Arrastrar XML o ZIP al card del diario de compras. Detecta
automáticamente XMLs DIAN y extrae partner, líneas, CUFE y
tipo de documento.

## Eventos RADIAN

Desde factura de proveedor confirmada con CUFE:

1. **030** - Acuse de recibo.
2. **032** - Recibo del bien/servicio.
3. **033** - Aceptación expresa, o **031** - Reclamo.

Flujo secuencial validado. Estado RADIAN en "Otra información".

## PDF (Representación gráfica)

Incluye: denominación DIAN, info fiscal emisor/receptor,
QR DIAN, CUFE/CUDE, mensaje de resolución, referencia NC/ND,
forma de pago.

---

Copyright (C) 2025 IKU Solutions - Yan Chirino <yan.chirino@iku.solutions>
Licencia AGPL-3.0 o posterior (http://www.gnu.org/licenses/agpl).
