{
    'name': 'Sales Margin Report ',
    'version': '0.1',
    'summary': 'Sales margin Report',
    'description': """ Sales Margin""",
    'category': 'sales',
    'author': 'Biniyam k',
    'website': 'mailto:biniyamkg@gmail.com',
    'license': 'LGPL-3',
    'depends': ['sale_margin','sale_management', 'sale', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'report/bk_sales_margin_report.xml',
        'wizard/bk_sales_profit_report_wizard_view.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
}
