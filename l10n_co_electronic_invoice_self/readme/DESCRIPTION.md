Integración directa con los servicios web de la DIAN para la emisión de
facturación electrónica colombiana en modo **software propio**.

Funcionalidades:

- Generación de XML UBL 2.1 con extensiones DIAN
- Firma digital XAdES-EPES y envelope SOAP con WS-Security
- Envío SendTestSetAsync (habilitación) y SendBillSync (producción)
- Consulta de estado: GetStatusZip y GetStatus (por CUFE)
- Consulta de rangos de numeración y clave técnica (GetNumberingRange)
- Generación de AttachedDocument con CDATA
- Eventos RADIAN con flujo secuencial (030, 031, 032, 033)
- Importación de facturas de proveedor desde XML o ZIP
- Representación gráfica PDF según requisitos DIAN
- Generación de ZIP (PDF + XML) para envío por email

Modos de operación: **Demostración**, **Habilitación** y **Producción**.

Documentos soportados:

- Factura electrónica de venta (01)
- Factura electrónica de exportación (02)
- Nota crédito electrónica (91) con o sin referencia
- Nota débito electrónica (92)
- Documento soporte (05)
- Nota de ajuste documento soporte (95)

Copyright (C) 2025 IKU Solutions - Yan Chirino <yan.chirino@iku.solutions>
