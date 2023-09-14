# -*- coding: utf-8 -*-
from odoo import models, fields, api


class AppraisalSummary(models.Model):
    _inherit = 'hr.appraisal'
    summary_line_ids = fields.One2many('appraisal.summary.line', 'summary_line_id', string="Part lines")
    overall_performance_score = fields.Float(compute="_compute_overall_total", readonly=True, store=True, tracking=True)
    overall_adjectival_rating = fields.Char(compute="_compute_adj_rating", readonly=True, store=True, tracking=True)
    ratee_comment = fields.Html()
    rater_comment = fields.Html()
    rater_superior_comment = fields.Html()
    
    @api.model
    def default_get(self, fields):
        res = super(AppraisalSummary, self).default_get(fields)
        summary_lines = []
        summary_rec = self.env['appraisal.summary.line.type'].search([])
        for rec in summary_rec:
            line = (0, 0, {
                'summary_line_type_id': rec.id,
                's_overall_weight': 0,
            })
            summary_lines.append(line)
        res.update({
            'summary_line_ids': summary_lines,
        })
        return res

    @api.model
    def create(self, vals):
        if not vals.get('cycle'):
            vals['summary_line_id'] = vals['cycle']
        res = super(AppraisalSummary, self).create(vals)
        return res

    @api.depends('summary_line_ids.s_subtotal')
    def _compute_overall_total(self):
        for record in self:
            overall_performance_score = 0
            for line in record.summary_line_ids:
                overall_performance_score += line.s_subtotal
            record.update({
                'overall_performance_score': overall_performance_score,
            })

    def _search_merit_rating(self, perf_score, merit_yr):
        conditions = [
            ('merit_year', "=", merit_yr),
            ('rating_from', '<=', perf_score),
            ('rating_to', '>=', perf_score),
        ]
        return self.env['appraisal.merit'].search(conditions, limit=1).name

    @api.depends('overall_performance_score')
    def _compute_adj_rating(self):
        for record in self:
            if record.state not in ('approved', 'cancel'):
                overall_adjectival_rating = self._search_merit_rating(record.overall_performance_score, "DEFAULT")
                if not overall_adjectival_rating:
                    overall_adjectival_rating = "null"
            else:
                overall_adjectival_rating = record.overall_adjectival_rating
            record.update({
                'overall_adjectival_rating': overall_adjectival_rating,
            })


class AppraisalSummaryLine(models.Model):
    _name = 'appraisal.summary.line'
    _description = "Performance Area"

    summary_line_id = fields.Many2one('hr.appraisal', required=True, ondelete='cascade')
    state = fields.Selection(related='summary_line_id.state')
    s_total_weighted_rating = fields.Float(string="Total Weighted Rating", compute='_compute_total_wr', readonly=True, tracking=5)
    s_overall_weight = fields.Float(string="Overall Weight")
    s_subtotal = fields.Float(string="Subtotal", compute='_compute_total_wr', readonly=True)
    sequence = fields.Integer('Sequence', default=10)
    summary_line_type_id = fields.Many2one('appraisal.summary.line.type', string="Performance Area")
    lock = fields.Boolean(related='summary_line_id.lock')

    @api.depends('summary_line_id.kra_total_weighted_rating', 'summary_line_id.c_total_weighted_rating', 's_overall_weight')
    def _compute_total_wr(self):
        for record in self:
            if record.summary_line_type_id.sequence == 1:
                record.s_total_weighted_rating = record.summary_line_id.kra_total_weighted_rating
                record.s_subtotal = record.summary_line_id.kra_total_weighted_rating * record.s_overall_weight
            elif record.summary_line_type_id.sequence == 2:
                record.s_total_weighted_rating = record.summary_line_id.c_total_weighted_rating
                record.s_subtotal = record.summary_line_id.c_total_weighted_rating * record.s_overall_weight
            else:
                record.s_total_weighted_rating = 0
                record.s_subtotal = 0


class AppraisalSummaryLineType(models.Model):
    _name = 'appraisal.summary.line.type'
    _description = "Type of a summary line"
    _order = "sequence"

    name = fields.Char(required=True)
    sequence = fields.Integer('Sequence', default=10)

    
class AppraisalMerit(models.Model):
    _name = 'appraisal.merit'
    _description = "Merit Rating Table"
    _order = "sequence, id"

    name = fields.Char(string="Adjectival Rating")
    sequence = fields.Integer('Sequence', default=10)
    merit_rating = fields.Integer()
    rating_from = fields.Float()
    rating_to = fields.Float()
    merit_year = fields.Char()
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, required=True)