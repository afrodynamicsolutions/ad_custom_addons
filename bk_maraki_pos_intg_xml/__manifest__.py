{
    'name': 'Maraki PoS Integration',
    'version': '17.0.1.0.0',
    'summary': 'MARAKI PoS XML Based Integration',
    'description': """MARAKI PoS XML Based Integration""",
    'category': 'Point of Sale',
    'author': 'Biniyam k',
    'website': 'mailto:biniyamkg@gmail.com',
    'license': 'LGPL-3',
    'depends': ['point_of_sale', 'web'],
    'data': [
        'views/inherit_pos_order_view.xml',
        'views/bk_pos_invoice_dump_xml.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
}
