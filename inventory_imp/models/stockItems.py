from odoo import models, fields, _, api
import re
from odoo.exceptions import ValidationError


class StokeMoveWithTax(models.Model):
    _inherit = "stock.move"
    customs_id = fields.Char(string="Customs ID")


class codeChange(models.Model):
    _inherit = "account.account"

    @api.constrains('code')
    def _check_account_code(self):
        ACCOUNT_REGEX = re.compile(r'^[A-Za-z0-9._-]+$')
        for account in self:
            if not re.match(ACCOUNT_REGEX, account.code):
                raise ValidationError(_(
                    "The account code can only contain alphanumeric characters and dots."
                ))
