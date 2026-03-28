from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


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

    analytic_readonly = fields.Boolean(
        string='Analytic Readonly',
        compute='_compute_analytic_readonly',
        store=False,
        help='True if analytic distribution is locked because it comes from a source document (PO/SO).',
    )

    def _compute_analytic_readonly(self):
        """
        Lock header analytic field if picking is linked to a PO or SO.
        Note: per-line analytic from PO lines is always readonly when linked to PO.
        We avoid @api.depends on sale_id since it only exists when sale_stock is installed.
        """
        for picking in self:
            has_po = bool(picking.purchase_id)
            has_so = bool(picking._get_sale_id())
            picking.analytic_readonly = has_po or has_so

    def _get_sale_id(self):
        """Safely return sale_id — returns False if sale_stock not installed."""
        self.ensure_one()
        return self._fields.get('sale_id') and self.sale_id or False

    def _get_po_line_analytic_for_move(self, move):
        """
        Find the analytic_distribution on the purchase.order.line
        linked to this stock.move (via purchase_line_id).
        Returns None if not found.
        """
        self.ensure_one()
        # stock.move has purchase_line_id when linked to a PO line
        po_line = getattr(move, 'purchase_line_id', None)
        if po_line and hasattr(po_line, 'analytic_distribution') and po_line.analytic_distribution:
            return po_line.analytic_distribution
        return None

    def _get_so_line_analytic_for_move(self, move):
        """
        Find the analytic_distribution on the sale.order.line
        linked to this stock.move (via sale_line_id).
        Returns None if not found.
        """
        self.ensure_one()
        so_line = getattr(move, 'sale_line_id', None)
        if so_line and hasattr(so_line, 'analytic_distribution') and so_line.analytic_distribution:
            return so_line.analytic_distribution
        return None

    def _get_source_document_analytic(self):
        """
        Return a 'common' analytic_distribution from source document at header level.
        Used only to decide if header field should be readonly.
        For actual per-move sync, use _sync_analytic_from_source().
        """
        self.ensure_one()
        # Check if any move has a PO line analytic
        for move in self.move_ids:
            analytic = self._get_po_line_analytic_for_move(move)
            if analytic:
                return analytic
        # Check SO lines
        for move in self.move_ids:
            analytic = self._get_so_line_analytic_for_move(move)
            if analytic:
                return analytic
        return None

    @api.onchange('analytic_distribution')
    def _onchange_analytic_distribution(self):
        """Propagate header analytic distribution to all move lines."""
        for picking in self:
            if picking.analytic_distribution:
                for move in picking.move_ids:
                    move.analytic_distribution = picking.analytic_distribution

    def _sync_analytic_from_source(self):
        """
        For each move line:
        - If linked to a PO line or SO line → get analytic from that line
        - Otherwise → keep manual analytic as-is
        Also update the header field to reflect the first found analytic (for display).
        """
        self.ensure_one()
        first_analytic = None
        for move in self.move_ids:
            analytic = (
                self._get_po_line_analytic_for_move(move)
                or self._get_so_line_analytic_for_move(move)
            )
            if analytic:
                move.analytic_distribution = analytic
                if not first_analytic:
                    first_analytic = analytic
        # Update header field for display
        if first_analytic:
            self.analytic_distribution = first_analytic

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for picking in records:
            picking._sync_analytic_from_source()
        return records

    def write(self, vals):
        result = super().write(vals)
        if 'purchase_id' in vals or 'sale_id' in vals:
            for picking in self:
                picking._sync_analytic_from_source()
        return result

    def button_validate(self):
        """Override to sync analytic from PO/SO lines then create analytic lines."""
        for picking in self:
            # Sync from PO/SO lines first
            picking._sync_analytic_from_source()
            # For standalone moves with no PO/SO: propagate header to lines that have none
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
