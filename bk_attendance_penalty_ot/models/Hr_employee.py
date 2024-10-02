from odoo import fields, models, api


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    def get_total_absence_deduction(self, date_from, date_to):
        absence_report = self.env['hr.employee.absent.report'].search([
            ('start_date', '>=', date_from),
            ('end_date', '<=', date_to),
        ], limit=1)
        deduction_amount = absence_report.absent_ids.search([('employee_id', '=', self.id)], limit=1)
        return deduction_amount.total_deduction if deduction_amount else 0.0

    def get_total_overtime_list(self, date_from, date_to):
        absence_report = self.env['hr.employee.absent.report'].search([
            ('start_date', '>=', date_from),
            ('end_date', '<=', date_to),
        ], limit=1)

        # Get overtime hours
        overtime_hours = absence_report.overtime_ids.search_read(
            [('employee_id', '=', self.id)],
            fields=['ot_hrs_normal', 'ot_hrs_night', 'ot_hrs_weekend', 'ot_hrs_holiday'],
            limit=1
        )
        or_lit = []
        if len(overtime_hours):
            for record in overtime_hours:
                filtered_record = {key: value for key, value in record.items() if key != 'id'}
                or_lit.append(filtered_record)
        return or_lit

