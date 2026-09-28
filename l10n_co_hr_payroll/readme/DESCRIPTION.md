Nómina Colombia
===============

Este módulo liquida la **nómina colombiana** sobre el motor de nómina de OCA
(`payroll`), funcionando tanto en Odoo Community como en Odoo Enterprise.

Características principales:

- **Estructura salarial mensual** con las categorías de reglas propias de
  Colombia: salario básico, otros devengados salariales, devengados no
  salariales, deducciones, neto, seguridad social a cargo del empleador,
  aportes parafiscales y provisiones de prestaciones sociales.
- **Salario mínimo 2026**: SMMLV (1.750.905 COP) y auxilio de transporte
  (249.095 COP) configurables por compañía, con valores legales por defecto.
- **Auxilio de transporte** automático solo para salarios hasta 2 SMMLV; no
  constituye salario ni hace parte del IBC, pero sí de la base de prima y
  cesantías.
- **IBC (Ingreso Base de Cotización)**: salario + horas extras + comisiones +
  otros devengados salariales. El auxilio de transporte no se incluye.
- **Deducciones del trabajador**: salud (4%) y pensión (4%) sobre el IBC.
- **Seguridad social a cargo del empleador**: salud (8,5%), pensión (12%) y
  ARL según la clase de riesgo del contrato (I=0,522%, II=1,044%, III=2,436%,
  IV=4,350% y V=6,960%).
- **Aportes parafiscales**: Caja de Compensación Familiar (4%), SENA (2%) e
  ICBF (3%) sobre el IBC, con **exoneración** (art. 114-1 del Estatuto
  Tributario, Ley 1819 de 2016) cuando todos los trabajadores ganan menos de
  10 SMMLV: se exoneran el 8,5% de salud del empleador, el SENA y el ICBF.
- **Provisiones de prestaciones sociales**: prima de servicios (8,33%),
  cesantías (8,33%), intereses a las cesantías (1% mensual) y vacaciones
  (4,17%).
- **Entradas por "inputs"** en la nómina para horas extras y recargos,
  comisiones, otros devengados salariales y otras deducciones (libranzas,
  embargos).
- **Desprendible de nómina** (reporte PDF en español) que muestra el
  devengado, las deducciones, el neto a pagar y el costo total para el
  empleador.