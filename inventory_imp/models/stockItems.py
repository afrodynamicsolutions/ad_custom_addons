from odoo import models, fields, _, api
import re
from odoo.exceptions import ValidationError


class StokeMoveWithTax(models.Model):
    _inherit = "stock.move"
    customs_id = fields.Char(string="Customs ID")