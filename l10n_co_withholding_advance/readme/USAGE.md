## Configuración

1. Instale el módulo desde el menú de Aplicaciones
2. Vaya a **Contabilidad > Configuración > Ajustes**
3. En la sección **Autorenta**, active la opción **Autorretención en Facturas de Clientes**
4. Configure los siguientes parámetros:
   - **Tasa de autorretención (%)**: Ingrese el porcentaje aplicable según la normativa colombiana (por ejemplo, 1.20% para autorretención de renta)
   - **Cuenta de autorretención débito**: Seleccione la cuenta contable que se usará para el débito (típicamente una cuenta de activo o gasto)
   - **Cuenta de autorretención crédito**: Seleccione la cuenta contable que se usará para el crédito (típicamente una cuenta de pasivo o de retenciones por pagar)

## Operación Automática

Una vez configurado, el módulo opera automáticamente:

- **En Facturas de Venta**: Al crear o modificar una factura de cliente, el sistema calcula automáticamente la autorretención
- **Cálculo**: El monto se calcula como: `Base Imponible × Tasa de Autorretención / 100`
- **Asientos Contables**: Se crean automáticamente las líneas contables correspondientes
- **Notas Crédito**: En notas crédito de cliente, los asientos se invierten automáticamente

## Ejemplo Práctico

Si tiene una factura de venta con:
- Base imponible: $10,000,000 COP
- Tasa de autorretención configurada: 1.20%

El sistema creará automáticamente:
- Línea de débito: $120,000 COP en la cuenta de autorretención débito
- Línea de crédito: $120,000 COP en la cuenta de autorretención crédito

## Verificación

Para verificar que la autorretención se está aplicando correctamente:

1. Cree o abra una factura de cliente
2. Verifique que exista una línea de tipo "tax" con la cuenta de autorretención configurada
3. Confirme que el monto corresponda al porcentaje configurado sobre la base imponible

## Notas Importantes

- El módulo solo aplica autorretención en documentos de tipo **Factura de Cliente** (`out_invoice`) y **Nota Crédito de Cliente** (`out_refund`)
- La autorretención NO se aplica si no hay líneas de productos en la factura
- Los cálculos se registran en los logs de Odoo para facilitar la auditoría
