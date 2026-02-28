{
    'name': 'VD Data Migration',
    'version': '18.0.1.0.0',
    'category': 'Tools',
    'summary': 'Migrate data between Odoo 18.0 instances via JSON-RPC',
    'description': """
VD Data Migration
=================
Migrate records between two Odoo 18.0 instances via JSON-RPC.

Features:
- Field mapping with source/target comparison
- Many2one / Many2many automatic resolution
- Frontend-driven per-record import with real-time progress
- Start from any batch number (resume support)
    """,
    'author': 'Vlad Lavrenko',
    'depends': ['base', 'web'],
    'application': True,
    'installable': True,
    'license': 'LGPL-3',
    'data': [
        'security/security_groups.xml',
        'security/ir.model.access.csv',
        'wizard/migration_wizard_views.xml',
        'views/menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            # M7: Owl progress widget
            # 'vd_data_migration/static/src/js/migration_progress_widget.js',
            # 'vd_data_migration/static/src/xml/migration_progress_widget.xml',
            # 'vd_data_migration/static/src/css/migration_progress_widget.css',
        ],
    },
}
