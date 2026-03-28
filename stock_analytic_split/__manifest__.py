{
    'name': 'Stock Analytic Distribution',
    'version': '18.0.4.0.0',
    'category': 'Inventory/Inventory',
    'summary': 'Analytic distribution widget on stock moves — auto-sync from PO/SO',
    'description': """
Stock Analytic Distribution
============================
Adds analytic distribution field on each stock move line,
using the exact same widget as invoice lines (popup with accounts and percentages).

Features:
- Analytic dropdown on each product line in transfers
- Same UX as account.move.line (invoices)
- Automatically creates analytic lines upon transfer validation
- Arabic translation included
- Header-level analytic distribution that propagates to all lines automatically
- Per-line override still supported
- Auto-sync from source document (PO/SO): analytic is pulled automatically and field is locked
- Manual edit preserved for standalone transfers (no PO/SO linked)
- Works with or without sale_stock module installed
    """,
    'author': 'Haytham Afify',
    'website': 'https://github.com/haythamafify',
    'images': ['static/description/banner.png'],
    'depends': [
        'stock',
        'analytic',
        'stock_account',
        'purchase_stock',
    ],
    'data': [
        'views/stock_picking_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
