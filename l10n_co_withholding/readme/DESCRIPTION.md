Retención en la Fuente para Colombia
=====================================

Este módulo implementa el soporte para **retención en la fuente** (RteFte),
**ReteIVA** y **ReteICA** en la localización contable de Colombia.

La retención en la fuente es el mecanismo mediante el cual el Estado colombiano
recauda anticipadamente impuestos a través de los agentes retenedores.

Características principales:

- **Configuración en la compañía**: Define si la empresa es agente de retención
  y las retenciones por defecto (RteFte, ReteIVA, ReteICA)
- **Clasificación de partners**: Régimen tributario, tipo de persona, gran
  contribuyente, autorretenedor
- **Posiciones fiscales automáticas**: Con mapeo de cuentas para desactivar
  retenciones según el régimen del proveedor (Régimen Simple, No Contribuyente)
- **Impuestos con conceptos**: Cada impuesto de retención tiene asociado un
  concepto tributario (honorarios, servicios, compras, etc.)
- **Cuantías mínimas**: Validación automática de la base mínima en UVT
  (configurable vía parámetro del sistema)
- **Cálculo automático**: Botón "Calcular Retenciones" en facturas que aplica
  las retenciones según la configuración de la compañía y el partner
- **Soporte para ventas y compras**: Aplica retenciones tanto en facturas de
  proveedor como de cliente
- **Integración con factura electrónica**: Los impuestos negativos se reportan
  correctamente como WithholdingTaxTotal en el EDI UBL
