# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': "Payment Provider: PayWay",
    'version': '1.0',
    'author': 'Tep Keven',
    'email': 'teapkevin@gmail.com',
    'category': 'Accounting/Payment Providers',
    'sequence': 351,
    'summary': "A payment provider based in Cambodia.",
    'description': "This is ABA PayWay payment provider with 3 payment options",  # Non-empty string to avoid loading the README file.
    'depends': ['payment'],
    'data': [
        'views/payment_payway_templates.xml',
        'views/payment_provider_views.xml',

        'data/payment_method_data.xml',
        'data/payment_provider_data.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
    'license': 'LGPL-3',
}
