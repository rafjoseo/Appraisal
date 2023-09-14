# -*- coding: utf-8 -*-
import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class AppraisalKRA(models.Model):
    _inherit = ['hr.appraisal']
    
    cycle = fields.Many2one('appraisal.cycle', string='Performance Cycle', required=True, domain="[('locked','=',False)]")
    description = fields.Text()
    job_title = fields.Char(related='employee_id.job_title')
    salary_grade = fields.Char()
    years_in_the_position = fields.Float()
    years_in_the_company = fields.Float()
    division = fields.Many2one(related='department_id.parent_id', string="Division")
    date_close = fields.Date(string='Appsraisal Deadline', required=True, readonly=True, related='cycle.appraisal_deadline')
    appraisal_save = fields.Boolean()
    manager_user_ids = fields.Many2many('res.users', 'appraisal_manager_user_rel', 'hr_appraisal_id', domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    rating_required = fields.Boolean(compute='_compute_rating_required')
    lock = fields.Boolean(compute='_compute_lock')
    superior_feedback_published = fields.Boolean(string="Superior Feedback Published", tracking=True)
    
    @api.depends('cycle.rating_start','cycle')
    def _compute_rating_required(self):
        self.ensure_one()
        if self.cycle.rating_start:
            to_compare_date = self.cycle.rating_start
            current_date = fields.Date.today()
            for record in self:
                record.rating_required = current_date >= to_compare_date
        else:
            self.rating_required = False
            
    @api.depends('cycle.lock_date','cycle')
    def _compute_lock(self):
        if self.cycle.lock_date:
            for record in self:
                record.lock = record.cycle.locked
        else:
            self.lock = False
            
    @api.onchange('manager_ids')
    def _onchange_manager_ids(self):
        self = self.sudo()       
        
        for record in self:
            for line in record.manager_ids:
                manager = record.env['hr.employee'].browse(line.user_id)
                if not manager:
                    raise ValidationError(_('The selected manager does not correspond to an existing user.'))
        
        managers = self.manager_ids.mapped(lambda lm: lm.user_id)
        if self.manager_ids:
            self.manager_user_ids = managers
            
    @api.constrains('manager_ids')
    def _check_manager_related_user(self):
        for record in self:
            for line in record.manager_ids:
                manager = record.env['hr.employee'].browse(line.user_id)
                if not manager:
                    raise ValidationError(_('The selected manager does not correspond to an existing user.'))

    @api.model
    def create(self, vals):
        result = super(AppraisalKRA, self).create(vals)
        result.sudo().write({'appraisal_save': True})
        return result
    
    cadg = fields.Binary(string="CADG", compute='_compute_appraisal_instruction')
    instruction = fields.Binary(string="Instruction", compute='_compute_appraisal_instruction')
    
    def _compute_appraisal_instruction(self):
        instruction = self.env['ir.config_parameter'].sudo().get_param('hr_appraisal.instruction')
        cadg = self.env['ir.config_parameter'].sudo().get_param('hr_appraisal.cadg')
        for record in self:
            record.instruction = instruction
            record.cadg = cadg
    
    kra_line_ids = fields.One2many('appraisal.kra.line', 'kra_line_id', string="KRA lines")
    competency_line_ids = fields.One2many('appraisal.competency.line', 'competency_line_id', string="Competency lines")
    overall_weight = fields.Float()
    subtotal = fields.Float()
    kra_total_weight = fields.Float(string="KRA Total Weight", readonly=True, tracking=True)
    kra_total_weighted_rating = fields.Float(string="KRA Total Weighted Rating", compute='_compute_total_wr_kra', readonly=True, tracking=True)
    c_total_weight = fields.Float(string="Competencies Total Weight", readonly=True, tracking=True)
    c_total_weighted_rating = fields.Float(string="Competencies Total Weighted Rating", compute='_compute_total_wr_c', readonly=True, tracking=True)
    rater_superior_comment = fields.Text()
    
    @api.depends('kra_line_ids.rating_b')
    def _compute_total_wr_kra(self):
        for record in self:
            kra_total_weighted_rating = kra_total_weight = 0
            for line in record.kra_line_ids:
                kra_total_weighted_rating += line.weighted_rating
                kra_total_weight += line.weight_a
            record.update({
                'kra_total_weighted_rating': kra_total_weighted_rating,
                'kra_total_weight': kra_total_weight,
            })

    @api.depends('competency_line_ids.rating')
    def _compute_total_wr_c(self):
        for record in self:
            c_total_weighted_rating = c_total_weight = 0
            for line in record.competency_line_ids:
                c_total_weighted_rating += line.weighted_rating
                c_total_weight += line.weight
            record.update({
                'c_total_weighted_rating': c_total_weighted_rating,
                'c_total_weight': c_total_weight,
            })

    
class AppraisalKRALine(models.Model):
    _name = 'appraisal.kra.line'
    _description = "KRA line of an appraisal"

    sequence = fields.Integer('Sequence', default=10)
    kra_line_id = fields.Many2one('hr.appraisal', required=True, ondelete='cascade')
    name = fields.Char()
    state = fields.Selection(related='kra_line_id.state')
    rating_required = fields.Boolean(related='kra_line_id.rating_required')
    lock = fields.Boolean(related='kra_line_id.lock')
    division_objective = fields.Text()
    individual_objective = fields.Text()
    measures = fields.Text()
    weight_a = fields.Float()
    achievement = fields.Html()
    rating_b = fields.Float()
    weighted_rating = fields.Float(compute='_compute_total', store=True)

    @api.depends('weight_a', 'rating_b')
    def _compute_total(self):
        for record in self:
            record.weighted_rating = record.weight_a * record.rating_b
            

class CompetencyLine(models.Model):
    _name = 'appraisal.competency.line'
    _description = "Competency line of an employee"
    _order = "line_type_id, date_end desc, date_start desc"

    competency_line_id = fields.Many2one('hr.appraisal', required=True, ondelete='cascade')
    name = fields.Char()
    state = fields.Selection(related='competency_line_id.state')
    date_start = fields.Date()
    date_end = fields.Date()
    action = fields.Text()
    result = fields.Text()
    kra_link = fields.Text()
    weight = fields.Float()
    rating = fields.Float()
    weighted_rating = fields.Float(compute='_compute_total', store=True, digits=(16, 2))
    rating_required = fields.Boolean(related='competency_line_id.rating_required')
    lock = fields.Boolean(related='competency_line_id.lock')
    description = fields.Text()
    line_type_id = fields.Many2one('appraisal.competency.line.type', string="Type")
    display_type = fields.Selection([('classic', 'Classic')], string="Display Type", default='classic', readonly=True)
    
    @api.depends('weight', 'rating')
    def _compute_total(self):
        for record in self:
            record.weighted_rating = record.weight * record.rating

    
class ComptetencyLineType(models.Model):
    _name = 'appraisal.competency.line.type'
    _description = "Type of a competency line"
    _order = "sequence"

    name = fields.Char(required=True)
    sequence = fields.Integer('Sequence', default=10)
  
    
class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    appraisal_instruction = fields.Binary()  
    appraisal_cadg = fields.Binary()
    
    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].set_param('hr_appraisal.instruction', self.appraisal_instruction)
        self.env['ir.config_parameter'].set_param('hr_appraisal.cadg', self.appraisal_cadg)
        return res
    
    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        instruction = ICPSudo.get_param('hr_appraisal.instruction')
        cadg = ICPSudo.get_param('hr_appraisal.cadg')
        res.update(
            appraisal_instruction = instruction,
            appraisal_cadg = cadg,
        )
        return res
    
      
class AppraisalCycle(models.Model):
    _name = 'appraisal.cycle'
    sequence = fields.Integer('Sequence', default=0)
    name = fields.Char(string='Performance Cycle')
    appraisal_deadline = fields.Date()
    rating_start = fields.Date()
    lock_date = fields.Date()
    override_lock_date = fields.Date()
    locked = fields.Boolean(compute='_compute_locked', store=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    
    @api.depends('lock_date', 'override_lock_date')
    def _compute_locked(self):
        current_date = fields.Date.today()
        if self.lock_date:
            for record in self:
                if not record.override_lock_date:
                    record.locked = record.lock_date <= current_date
                else:
                    record.locked = record.override_lock_date <= current_date
        else:
            self.locked = False