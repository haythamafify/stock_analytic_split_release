from odoo import fields, models


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    stock_move_id = fields.Many2one(
        comodel_name='stock.move',
        index=True,
        ondelete='set null',
    )
    stock_picking_id = fields.Many2one(
        comodel_name='stock.picking',
        index=True,
        ondelete='set null',
    )
