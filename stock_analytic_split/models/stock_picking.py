from odoo import models, _


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        """Override to create analytic lines after validation."""
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
