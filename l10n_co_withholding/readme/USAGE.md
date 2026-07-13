Configuración de la Compañía
-----------------------------

1. Instale el módulo desde el menú de Aplicaciones
2. Vaya a **Configuración > Empresas** y abra su empresa
3. En la pestaña **"Retenciones Colombia"**:
   - Active **"Agente de Retención"** si su empresa actúa como agente
   - Configure las retenciones por defecto:
     - **ReteFte por Defecto**: Impuestos de retención en la fuente
     - **ReteIVA por Defecto**: Impuestos de retención de IVA
     - **ReteICA por Defecto**: Impuestos de retención de ICA

Configuración del Valor UVT
----------------------------

El valor de la UVT se configura como parámetro del sistema:

1. Vaya a **Configuración > Parámetros del Sistema**
2. Busque el parámetro `l10n_co_withholding.uvt_value`
3. Actualice el valor anualmente según la resolución de la DIAN
   (por defecto: 52374 para 2026)

Configuración de Partners
--------------------------

1. Abra un contacto (proveedor o cliente)
2. En la pestaña **"Retenciones Colombia"**:
   - **Régimen Tributario**: Ordinario, Simple o No Contribuyente
   - **Tipo de Persona**: Natural o Jurídica
   - **Gran Contribuyente**: Si aplica
   - **Autorretenedor**: Si aplica

Uso - Calcular Retenciones en Facturas
---------------------------------------

1. Cree una factura (de proveedor o de cliente)
2. Agregue líneas de producto/servicio
3. Haga clic en el botón **"Calcular Retenciones"** en la barra superior
4. El sistema calculará automáticamente las retenciones aplicables según:
   - Configuración de la compañía (agente de retención + retenciones por defecto)
   - Régimen del partner (Simple no aplica RteFte, No Contribuyente no aplica nada)
   - Tipo de persona del partner
   - Cuantías mínimas en UVT

Posiciones Fiscales
-------------------

El módulo incluye posiciones fiscales preconfiguradas con mapeo de cuentas:

- **Régimen Simple (Sin ReteFte)**: Elimina las retenciones de renta (RteFte)
  pero mantiene ReteIVA y ReteICA. Mapea cuentas de pasivo (236xxx) a activo
  (135xxx)
- **No Contribuyente (Sin Retenciones)**: Elimina todas las retenciones
  (RteFte, ReteIVA, ReteICA). Mapea cuentas de pasivo a activo

Asigne la posición fiscal correspondiente al partner para que las retenciones
se ajusten automáticamente.
