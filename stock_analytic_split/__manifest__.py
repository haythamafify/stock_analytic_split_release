{
    'name': 'Stock Analytic Distribution',
    'version': '18.0.3.0.0',
    'category': 'Inventory/Inventory',
    'summary': 'Analytic distribution widget on stock move lines (like invoices)',
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
    """,
    'author': 'Haytham Afify',
    'website': 'https://github.com/haythamafify',
    'images': ['static/description/banner.png'],
    'depends': [
        'stock',
        'analytic',
        'stock_account',
    ],
    'data': [
        'views/stock_picking_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
