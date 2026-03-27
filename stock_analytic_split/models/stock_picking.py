from odoo import models, fields, api, _


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    analytic_distribution = fields.Json(
        string='Analytic Distribution',
        help='Set a default analytic distribution for all lines. '
             'It will be applied automatically to all move lines.',
    )

    analytic_precision = fields.Integer(
        store=False,
        default=lambda self: self.env['decimal.precision'].precision_get('Percentage Analytic'),
    )

    @api.onchange('analytic_distribution')
    def _onchange_analytic_distribution(self):
        """Propagate header analytic distribution to all move lines."""
        for picking in self:
            if picking.analytic_distribution:
                for move in picking.move_ids:
                    move.analytic_distribution = picking.analytic_distribution

    def button_validate(self):
        """Override to create analytic lines after validation."""
        # Before validating, propagate header distribution to lines that have none
        for picking in self:
            if picking.analytic_distribution:
                for move in picking.move_ids.filtered(lambda m: not m.analytic_distribution):
                    move.analytic_distribution = picking.analytic_distribution
        result = super().button_validate()
        for picking in self:
            if picking.state == 'done':
                picking._create_analytic_lines_for_moves()
        return result

    def _create_analytic_lines_for_moves(self):
        """Create analytic lines for all done moves that have analytic_distribution."""
        self.ensure_one()
        for move in self.move_ids.filtered(
            lambda m: m.state == 'done' and m.analytic_distribution
        ):
            move._create_analytic_lines_from_distribution()

    def action_view_analytic_lines(self):
        """Open analytic lines related to this picking."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Analytic Lines - %s') % self.name,
            'res_model': 'account.analytic.line',
            'view_mode': 'list,form',
            'domain': [
                ('stock_picking_id', '=', self.id),
                ('company_id', '=', self.company_id.id),
            ],
        }
