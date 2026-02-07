Este módulo implementa el manejo automático de **autorretenciones anticipadas** en facturas de venta para la localización contable de Colombia.

La autorretención es un mecanismo tributario mediante el cual ciertas empresas están obligadas a retener y pagar directamente al Estado un porcentaje de sus ingresos, actuando como agentes retenedores sobre sí mismas.

Este módulo permite:

- **Configuración flexible**: Define las cuentas contables de débito y crédito para las autorretenciones
- **Tasa personalizable**: Configura el porcentaje de autorretención según las disposiciones legales vigentes
- **Cálculo automático**: Calcula automáticamente el valor de la autorretención basado en la base imponible de la factura
- **Integración contable**: Genera automáticamente las líneas contables correspondientes en facturas de venta y notas crédito
- **Soporte para notas crédito**: Invierte correctamente los asientos contables en las notas crédito
