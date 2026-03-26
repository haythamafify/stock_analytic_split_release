from odoo import models, fields
import logging

_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = 'stock.move'

    analytic_distribution = fields.Json(
        string='Analytic Distribution',
        help='Analytic accounts distribution for this stock move line.',
    )

    analytic_precision = fields.Integer(
        store=False,
        default=lambda self: self.env['decimal.precision'].precision_get('Percentage Analytic'),
    )

    def _create_analytic_lines_from_distribution(self):
        """Create analytic lines based on analytic_distribution after validation."""
        self.ensure_one()
        analytic_line_obj = self.env['account.analytic.line']
        distribution = self.analytic_distribution or {}

        if not distribution:
            return

        existing_lines = analytic_line_obj.search([('stock_move_id', '=', self.id)])
        existing_distribution_keys = {
            self._normalize_distribution_key(line._get_analytic_accounts().ids)
            for line in existing_lines
            if line._get_analytic_accounts()
        }

        total_cost = self._compute_move_cost()
        if not total_cost:
            _logger.warning(
                'No cost for move %s (product: %s). Skipping analytic lines.',
                self.id, self.product_id.display_name,
            )
            return

        for account_ids_key, percentage in distribution.items():
            if account_ids_key == '__update__':
                continue
            try:
                percentage = float(percentage or 0.0)
            except (TypeError, ValueError):
                _logger.warning(
                    'Invalid analytic distribution percentage %s on move %s. Skipping key %s.',
                    percentage, self.id, account_ids_key,
                )
                continue

            parsed = self._parse_distribution_accounts(account_ids_key)
            if not parsed:
                continue
            distribution_key, accounts = parsed
            if distribution_key in existing_distribution_keys:
                _logger.info(
                    'Analytic lines for distribution key %s already exist on move %s. Skipping.',
                    distribution_key, self.id,
                )
                continue

            if not percentage:
                continue

            analytic_vals = {
                'name': '%s - %s' % (self.picking_id.name or '', self.product_id.display_name),
                'account_id': accounts[:1].id,
                'amount': total_cost * percentage / 100.0,
                'date': (self.picking_id.date_done.date()
                         if self.picking_id and self.picking_id.date_done
                         else fields.Date.today()),
                'ref': self.picking_id.name if self.picking_id else '',
                'product_id': self.product_id.id,
                'unit_amount': self.quantity * percentage / 100.0,
                'product_uom_id': self.product_uom.id,
                'company_id': self.company_id.id,
                'stock_move_id': self.id,
                'stock_picking_id': self.picking_id.id,
            }
            for account in accounts:
                analytic_vals[account.plan_id._column_name()] = account.id

            analytic_line_obj.create(analytic_vals)
            existing_distribution_keys.add(distribution_key)

    def _parse_distribution_accounts(self, account_ids_key):
        try:
            account_ids = [int(aid.strip()) for aid in str(account_ids_key).split(',') if aid.strip()]
        except ValueError:
            _logger.warning(
                'Invalid analytic distribution key %s on move %s. Skipping.',
                account_ids_key, self.id,
            )
            return False

        if not account_ids:
            _logger.warning(
                'Empty analytic distribution key %s on move %s. Skipping.',
                account_ids_key, self.id,
            )
            return False

        normalized_ids = list(dict.fromkeys(account_ids))
        accounts = self.env['account.analytic.account'].browse(normalized_ids).exists()
        if len(accounts) != len(normalized_ids):
            _logger.warning(
                'Unknown analytic account in key %s on move %s. Skipping.',
                account_ids_key, self.id,
            )
            return False
        return self._normalize_distribution_key(normalized_ids), accounts

    def _normalize_distribution_key(self, account_ids):
        return ",".join(str(account_id) for account_id in sorted(set(account_ids)))

    def _compute_move_cost(self):
        """Get total cost. Uses valuation layers first, falls back to standard price."""
        self.ensure_one()
        cost = 0.0
        if self.stock_valuation_layer_ids:
            cost = sum(self.stock_valuation_layer_ids.mapped('value'))
        if not cost:
            qty = self.quantity
            if self.location_id.usage == 'internal' and self.location_dest_id.usage != 'internal':
                qty *= -1
            cost = self.product_id.standard_price * qty
        return cost
