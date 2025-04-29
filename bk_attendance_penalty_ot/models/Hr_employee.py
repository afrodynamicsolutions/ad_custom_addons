from odoo import  models, api


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    def get_total_absence_deduction(self, date_from, date_to):
        deduction_absent = self.env['hr.employee.absence'].search([('employee_id', '=', self.id),
                                                                   ('absent_report_id.start_date', '=', date_from),
                                                                   ('absent_report_id.end_date', '=', date_to),
                                                                   ('absent_report_id.state', '=', 'locked'),
                                                                   ], limit=1)

        return deduction_absent.total_deduction if deduction_absent else 0.0


    def get_commission(self, date_from, date_to):
        commission_list = self.env['bk.sales.commission'].search_read([
            ('employee_id', '=', self.id),
            ('report_id.start_date', '=', date_from),
            ('report_id.end_date', '=', date_to),
            ('report_id.state', '=', 'locked'),
        ], ['commission_amount'])
        if commission_list:
            sum_amount = sum(comm['commission_amount'] for comm in commission_list if comm.get('commission_amount'))
        else:
            sum_amount = 0

        return sum_amount

    def get_total_overtime_list(self, date_from, date_to):

        overtime_hours = self.env['hr.employee.overtime'].search_read([('employee_id', '=', self.id),
                                                                       ('ot_report_id.start_date', '=', date_from),
                                                                       ('ot_report_id.end_date', '=', date_to),
                                                                       ('ot_report_id.state', '=', 'locked'),
                                                                       ],
                                                                      fields=['ot_hrs_normal', 'ot_hrs_night',
                                                                              'ot_hrs_weekend', 'ot_hrs_holiday'],
                                                                      limit=1)
        or_lit = []
        if len(overtime_hours):
            for record in overtime_hours:
                filtered_record = {key: value for key, value in record.items() if key != 'id'}
                or_lit.append(filtered_record)

        return or_lit
