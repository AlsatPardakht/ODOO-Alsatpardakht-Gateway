# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'alsatpardakht Payment Acquirer',
    'version': '1.0',
    'category': 'Accounting/Payment Acquirers',
    'summary': 'Payment Acquirer: alsatpardakht Implementation',
    'author': 'Alsatpardakht',
    'website': 'https://www.Alsatpardakht.com',
    'support': 'support@Alsatpardakht.com',
    'description': """
alsatpardakht Payment Acquirer
""",
    'depends': ['payment'],
    'external_dependencies': {
        'python': ['urllib3', 'zeep', 'requests'],
    },
    'data': [
        'views/payment_alsatpardakht_templates.xml',
        'views/payment_view.xml',

        'data/payment_icon_data.xml',
        'data/payment_acquirer_data.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'payment_test/static/src/js/**/*',
        ],
    },
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'post_init_hook': 'create_missing_journal_for_acquirers',
    'uninstall_hook': 'uninstall_hook',
}
