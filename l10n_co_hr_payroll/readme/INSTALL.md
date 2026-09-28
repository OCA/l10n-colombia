Instalación
===========

El módulo depende del motor de nómina de la OCA (`payroll`), el backport libre
del módulo `hr_payroll` de Odoo Enterprise.

**Odoo Community**

1. Instale el addon `payroll` de la OCA (ramas `18.0` de
   `OCA/payroll <https://github.com/OCA/payroll>`_).
2. Instale este módulo normalmente (*Aplicaciones → Nómina*).

**Odoo Enterprise**

En Enterprise no se puede cargar `hr_payroll` (módulo propietario) junto con
una localización que herede de él, porque Odoo no soporta dependencias
alternativas entre módulos. La solución soportada y estándar en OCA es:

1. Instale el addon `payroll` de la OCA como reemplazo (drop-in) de
   `hr_payroll`: usa los **mismos modelos** (`hr.payslip`, `hr.salary.rule`,
   `hr.payroll.structure`, etc.).
2. Desinstale (o no instale) `hr_payroll` de Enterprise para evitar conflictos
   de definición de modelos.
3. Instale este módulo.

Con `payroll` de la OCA como motor, esta localización se comporta igual en
Community y en Enterprise.