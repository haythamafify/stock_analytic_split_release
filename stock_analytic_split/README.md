# Stock Analytic Distribution (`stock_analytic_split`)

Odoo 18 addon that brings the invoice-style **analytic distribution widget** to stock transfer move lines and creates analytic lines when transfers are validated.

## Features

- Adds `analytic_distribution` on `stock.move` lines in transfer forms.
- Uses the native `analytic_distribution` widget for percentage split by analytic accounts.
- On transfer validation (`button_validate`), creates `account.analytic.line` records from each done move distribution.
- Links analytic lines back to stock records through:
  - `account.analytic.line.stock_move_id`
  - `account.analytic.line.stock_picking_id`
- Includes Arabic translations (`i18n/ar.po`).

## Dependencies

- `stock`
- `analytic`
- `stock_account`

## Installation

1. Place this module in your Odoo addons path.
2. Update the app list.
3. Install **Stock Analytic Distribution**.

## Usage

1. Open a transfer (`Inventory > Operations > Transfers`).
2. On product lines, set values in the **Analytic** distribution column.
3. Validate the transfer.
4. Analytic lines are generated per distribution percentage for done moves.

## Technical Notes

- Distribution data is stored as JSON in `stock.move.analytic_distribution`.
- Cost source:
  - Uses `stock_valuation_layer_ids.value` when available.
  - Falls back to `product.standard_price * quantity` if valuation layers are missing.
- Duplicate distribution keys for the same move are skipped to avoid duplicate analytic lines.
- Multi-plan analytic splits are supported by mapping plan-specific columns on `account.analytic.line`.

## Module Structure

- `models/stock_move.py`: distribution field + analytic line creation logic.
- `models/stock_picking.py`: validation hook that triggers creation.
- `models/account_analytic_line.py`: stock relation fields.
- `views/stock_picking_views.xml`: injects analytic widget into transfer lines.

## License

LGPL-3
