{
    'name': 'Colombia - Terceros',
    'category': 'Localization',
    'version': '1.0',
    'author': 'Dominic Krimmer, Plastinorte S.A.S',
    'license': 'AGPL-3',
    'maintainer': 'dominic.krimmer@gmail.com',
    'website': 'https://www.plastinorte.com',
    'summary': 'Colombia Terceros: Extended Partner / Contact Module - Odoo 9.0',
    'images': ['images/main_screenshot.png'],
    'description': """
Colombia Terceros:
======================

    * Redesign of the contact form due to some local rules that have to apply
    * Additional fields: first name, second name, last name, second last name
    * Additional fields: Type of Person, Document Type, Document Number, Tributate regime, CIIU Code
    * Handling all kind of identification types that are relevant in Colombia
    * Intelligent form: Fields will be checked for correctness and completeness
    * Identification Number added into Tree View
    * Identification Number added into KanBan View
    * Visual Identifier for incomplete contacts in Kanban- and Tree view
    * Auto-Complete of NIT: Type in the NIT and the Verification Digit will be calculated automatically
    * Description of economic activities (CIIU Code), including the entire list to maintain it
    * Contacts can be found by Identification Number (e.g. NIT)
    * Added a complete list of all cities and departments in Colombia
    * Country, Department and Municipality Dependency Logic in order to avoid confusion of locations with the same name
    * Identification / Document-Type combination will be checked as it should be unique
    * All changes available in english (en_GB)

    """,
    'depends': [
        'account',
        'account_accountant',
        'base'
    ],
    'data': [
        'views/l10n_co_res_partner.xml',
        'views/ciiu.xml',
        'data/ciiu.csv',
        'data/l10n_states_co_data.xml',
        'data/l10n_cities_co_data.xml',
        'security/ir.model.access.csv'
    ],
    'installable': True,
}