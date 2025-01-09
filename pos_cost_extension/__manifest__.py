{
    "name": "Pos Cost Extension",
    "author": "Dagem Alemayehu",
    "version": "1.0",
    "category": "Invisible",
    "description": """
    This Module adds a functionality to Print a confirmed payslips from a batch payslip 
    """,
    "depends": ["point_of_sale"],

    'assets': {
        'point_of_sale._assets_pos': [
            "pos_cost_extension/static/src/**/*"

        ]
    },
    "licence": "LGPL-3"
}
