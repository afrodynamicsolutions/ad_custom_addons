from odoo import models, fields, api
from odoo.exceptions import ValidationError


class BkSalesCommissionConfig(models.Model):
    _name = 'bk.sales.commission.config'
    _description = 'Sales Commission Configuration'

    name = fields.Char(string="Reference", required=True)
    department_id = fields.Many2one('hr.department', string="Department", required=True)
    sales_amount = fields.Float(string="Sales Amount")
    pay_date = fields.Date(string="Pay Day")
    commission_rate = fields.Float(string="Commission Rate", required=True)
    employee_list_ids = fields.One2many('bk.sales.commission', 'commission_config_id', stirng="Commission Detail")
    included_employees = fields.Many2many('hr.employee', 'rel_included_employees', string="Included Employees")
    excluded_employees = fields.Many2many('hr.employee', 'rel_excluded_employees', string="Excluded Employees")

    @api.onchange('department_id')
    def _onchange_department_id(self):
        if self.department_id:
            employees = self.env['hr.employee'].search([('department_id', '=', self.department_id.id)])
            self.included_employees = employees - self.excluded_employees

    def generate_commission(self):
        if not self.pay_date:
            raise ValidationError("Payroll Date required !!")
        self.employee_list_ids.unlink()
        if not self.included_employees:
            self._onchange_department_id()

        # Loop through the included employees
        for employee in self.included_employees:
            if employee in self.excluded_employees:
                continue

            if len(self.included_employees):
                commission_amount = (self.sales_amount * self.commission_rate) / (100*len(self.included_employees))
            else:
                commission_amount = 0.0
            commission_record = self.env['bk.sales.commission'].create({
                'employee_id': employee.id,
                'remark': self.name,
                'commission_date': self.pay_date,
                'commission_amount': commission_amount,
                'department_id': self.department_id.id,
                'total_sales': self.sales_amount,
                'commission_rate': self.commission_rate,
                'commission_config_id': self.id,
            })

            self.employee_list_ids = [(4, commission_record.id)]

        return True

    def regenerate_commission(self):
        self.generate_commission()

    def clear_commission_list(self):
        commission_list = self.env['bk.sales.commission'].search([('commission_config_id', '=', self.id)])
        commission_list.unlink()


class BkSalesCommission(models.Model):
    _name = 'bk.sales.commission'
    _description = 'Sales Commission Record'

    employee_id = fields.Many2one('hr.employee', string="Employee", required=True)
    commission_date = fields.Date(string="Date", required=True)
    remark = fields.Char(string="Notes")

    commission_amount = fields.Float(string="Commission Amount")
    department_id = fields.Many2one('hr.department', string="Department")
    total_sales = fields.Float(string="Total Sales")
    commission_rate = fields.Float(string="Commission Rate")
    report_id = fields.Many2one("hr.employee.absent.report", string="Sales Commission Report")
    commission_config_id = fields.Many2one("bk.sales.commission.config", string=" Commission Config")

    @api.depends('total_sales', 'commission_rate')
    def _compute_commission_amount(self):
        for record in self:
            if record.total_sales and record.commission_rate:
                record.commission_amount = record.total_sales * (record.commission_rate / 100)


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
    # I might need to add new working
    new_working_hours = fields.Float(string="Other Monthly/Hrs", default=208.00)
    other_monthly_working_hours = fields.Float(string="Monthly Working Hours", compute='_compute_other_monthly_working_hours')
    change_working_hrs = fields.Boolean(string='Change Working Hours', default=False)

    @api.depends('report_report_id')
    def _compute_other_monthly_working_hours(self):
        for record in self:
            if record.report_report_id:
                record.other_monthly_working_hours = record.report_report_id.monthly_working_hours
            else:
                record.other_monthly_working_hours = 208.0  # Default

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
                total_missed_hours = (line.absence_days * 8) + line.absence_hours + (line.absence_minutes / 60.0)
                if line.change_working_hrs:
                    monthly_working_hours = line.new_working_hours
                    if not monthly_working_hours:
                        line.total_deduction = 0
                    else:
                        hourly_wage = contract.wage / monthly_working_hours
                        deduction_amount = hourly_wage * total_missed_hours
                        line.total_deduction = deduction_amount

                elif not line.change_working_hrs:
                    monthly_working_hours = line.absent_report_id.monthly_working_hours
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
    monthly_working_hours = fields.Float(string="Monthly Working Hours", default=208.0)
    state = fields.Selection([('draft', 'Draft'), ('locked', 'Apply to Payroll'), ('done', 'Locked')], string="Status", default="draft")
    absent_ids = fields.One2many("hr.employee.absence", 'absent_report_id', string="Absence Records")
    commission_ids = fields.One2many("bk.sales.commission", 'report_id', string="Sales Commission Records")

    overtime_ids = fields.One2many("hr.employee.overtime", 'ot_report_id', string="Overtime Records")
    total_absence_hours = fields.Float(string="Total Missed Hours", compute="_compute_total_absence_hours")
    total_deduction = fields.Float(string="Total Deduction", compute="_compute_total_deduction")
    duplicate_employees_text = fields.Text(string="Duplicated Employees", compute="_compute_duplicate_employees")

    _sql_constraints = [
        ('unique_start_end_date', 'unique(start_date, end_date)', 'The Start Date and End Date must be unique.')
    ]

    @api.depends('commission_ids')
    def _compute_total_commission(self):
        for report in self:
            total_commission = sum(commission.commission_amount for commission in report.commission_ids)
            report.total_commission = total_commission

    total_commission = fields.Float(string="Total Commission", compute="_compute_total_commission")

    def _populate_commission_records(self):
    
        self.ensure_one()
        # Get the commission configuration for the department
        commission_config = self.env['bk.sales.commission.config'].search([
            ('department_id', '=', self.department_id.id)
        ])

        # Create commission records for each employee in the department
        for emp in commission_config.included_employees:
            total_sales = emp.sales_ids.filtered(lambda sale: sale.date >= self.start_date and sale.date <= self.end_date).total_sales
            commission_rate = commission_config.commission_rate
            self.env['bk.sales.commission'].create({
                'employee_id': emp.id,
                'commission_date': self.end_date,
                'total_sales': total_sales,
                'commission_rate': commission_rate,
                'report_id': self.id
            })


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

        commission = self.env['bk.sales.commission'].search([
            ('commission_date', '>=', self.start_date),
            ('commission_date', '<=', self.end_date)
        ])
        # Update absent list
        self.absent_ids = [(5, 0, 0)]  # Clear existing records before populating
        absence_lines = [(4, absence.id) for absence in absences]
        self.write({'absent_ids': absence_lines})

        # update overtime list
        self.overtime_ids = [(5, 0, 0)]  # Clear existing records before populating
        overtime_lines = [(4, ot.id) for ot in overtime]
        self.write({'overtime_ids': overtime_lines})

        # update commission
        self.commission_ids = [(5, 0, 0)]  # Clear existing records before populating
        commission_lines = [(4, com.id) for com in commission]
        self.write({'commission_ids': commission_lines})

    def apply_to_payroll(self):
        self.state = "locked"



