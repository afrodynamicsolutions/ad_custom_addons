from odoo import models, fields, api


class HrEmployeeOvertime(models.Model):
    _name = 'hr.employee.overtime'
    _description = 'Employee Absence Record'
    _rec_name = 'employee_id'

    employee_id = fields.Many2one('hr.employee', string="Employee", required=True)
    payroll_date = fields.Date(string="Payroll Date", required=True)
    ot_hrs_normal = fields.Float(string="Normal worked Hours")
    ot_hrs_night = fields.Float(string="Night worked Hours")
    ot_hrs_weekend = fields.Float(string="Weekend worked Hours")
    ot_hrs_holiday = fields.Float(string="Holiday worked Hours")
    ot_report_id = fields.Many2one("hr.employee.absent.report", string="Report")

class HrEmployeeAbsence(models.Model):
    _name = 'hr.employee.absence'
    _description = 'Employee Absence Record'
    _rec_name = 'employee_id'

    employee_id = fields.Many2one('hr.employee', string="Employee", required=True)
    absence_days = fields.Float(string="Absent Days", required=True)
    absence_hours = fields.Integer(string="Absent Hours", required=True)
    absence_minutes = fields.Integer(string="Absent Minutes", required=True)
    absence_date = fields.Date(string="Payroll Date", required=True)
    total_missed_hours = fields.Float(string="Total Missed Hours", compute='_compute_total_absence_hours')
    absent_report_id = fields.Many2one("hr.employee.absent.report", string="Absent Report")
    report_report_id = fields.Many2one("hr.employee.absent.report", string="Absent Report")
    total_deduction = fields.Float(string="Deductible Amount", compute='_compute_deductible_amount')

    def _compute_total_absence_hours(self):
        for line in self:
            total_hours = 0.0
            total_hours = line.absence_days * 8 + line.absence_hours + (line.absence_minutes / 60)
            line.total_missed_hours = total_hours

    @api.depends('absent_report_id')
    def _compute_deductible_amount(self):
        for line in self:
            contract = self.env['hr.contract'].search([
                ('state', '=', 'open'),
                ('employee_id', '=', line.employee_id.id)
            ], limit=1)

            if contract and line.absent_report_id:
                monthly_working_hours = line.absent_report_id.monthly_working_hours
                total_missed_hours = (line.absence_days * 8) + line.absence_hours + (line.absence_minutes / 60.0)
                hourly_wage = contract.wage / monthly_working_hours
                deduction_amount = hourly_wage * total_missed_hours
                line.total_deduction = deduction_amount
            else:
                line.total_deduction = 0.0


class HrEmployeeAbsentReport(models.Model):
    _name = 'hr.employee.absent.report'
    _description = 'Employee Absence Summary Report'

    name = fields.Char(string="Reference", required=True, default=lambda self: self.env['ir.sequence'].next_by_code('hr.employee.absent.report'))
    start_date = fields.Date(string="Start Date", required=True)
    end_date = fields.Date(string="End Date", required=True)
    monthly_working_hours = fields.Float(string="Monthly Working Hours", default=240.0)
    state = fields.Selection([('draft', 'Draft'), ('locked', 'Apply to Payroll')], string="Status", default="draft")
    absent_ids = fields.One2many("hr.employee.absence", 'absent_report_id', string="Absence Records")

    overtime_ids = fields.One2many("hr.employee.overtime", 'ot_report_id', string="Overtime Records")
    total_absence_hours = fields.Float(string="Total Missed Hours", compute="_compute_total_absence_hours")
    total_deduction = fields.Float(string="Total Deduction", compute="_compute_total_deduction")
    duplicate_employees_text = fields.Text(string="Duplicated Employees", compute="_compute_duplicate_employees")

    _sql_constraints = [
        ('unique_start_end_date', 'unique(start_date, end_date)', 'The Start Date and End Date must be unique.')
    ]

    @api.depends('absent_ids')
    def _compute_duplicate_employees(self):
        for report in self:
            employee_count = {}
            duplicates = []
            for absence in report.absent_ids:
                employee = absence.employee_id.name
                if employee in employee_count:
                    employee_count[employee] += 1
                else:
                    employee_count[employee] = 1
            duplicates = [emp for emp, count in employee_count.items() if count > 1]
            if duplicates:
                report.duplicate_employees_text = ', '.join(duplicates)
            else:
                report.duplicate_employees_text = "No duplicates"

    @api.depends('absent_ids')
    def _compute_total_absence_hours(self):
        for report in self:
            total_hours = 0.0
            for absence in report.absent_ids:
                total_hours += absence.total_missed_hours
            report.total_absence_hours = total_hours

    @api.depends('total_absence_hours')
    def _compute_total_deduction(self):
        for report in self:
            total_deduction_amount = 0.0
            for absence in report.absent_ids:
                total_deduction_amount += absence.total_deduction
            report.total_deduction = total_deduction_amount

    @api.model
    def create(self, vals):
        report = super(HrEmployeeAbsentReport, self).create(vals)
        report._auto_populate_absences()
        return report

    def refresh_absences(self):
        for report in self:
            report._auto_populate_absences()

    def _auto_populate_absences(self):
        self.ensure_one()
        absences = self.env['hr.employee.absence'].search([
            ('absence_date', '>=', self.start_date),
            ('absence_date', '<=', self.end_date)
        ])
        overtime = self.env['hr.employee.overtime'].search([
            ('payroll_date', '>=', self.start_date),
            ('payroll_date', '<=', self.end_date)
        ])
        # Update absent list
        self.absent_ids = [(5, 0, 0)]  # Clear existing records before populating
        absence_lines = [(4, absence.id) for absence in absences]
        self.write({'absent_ids': absence_lines})

        # update overtime list
        self.overtime_ids = [(5, 0, 0)]  # Clear existing records before populating
        overtime_lines = [(4, ot.id) for ot in overtime]
        self.write({'overtime_ids': overtime_lines})

    def apply_to_payroll(self):
        self.state = "locked"

