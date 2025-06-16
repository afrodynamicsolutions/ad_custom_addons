{
    'name': 'POS Invoice XML Generator',
    'version': '1.0',
    'category': 'Point of Sale',
    'summary': 'Generate Order XML in POS frontend for offline use',
    'author': 'Biniyam K|info.biniyamkg@gmail.com',
    'depends': ['point_of_sale', 'web'],
    'data': [ ],
    'assets':{
            'point_of_sale._assets_pos': [
                "bk_custom_pos_sales_xml/static/src/js/pos_invoice_xml.js"
            ]
        },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
