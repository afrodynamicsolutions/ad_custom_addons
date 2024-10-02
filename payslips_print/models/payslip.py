from odoo import models, fields, api, tools, _


class BatchPayslipReport(models.AbstractModel):
    _name = 'report.payslips_print.payslip_report'

    def _get_report_values(self, docids, data=None):
        data = self.env['hr.payslip.run'].browse(docids)
        sorted_payslips= sorted(data[0].slip_ids,key= lambda slip : slip.employee_id.name)
        return {
            'docs': data,
            "payslips":sorted_payslips
        }
