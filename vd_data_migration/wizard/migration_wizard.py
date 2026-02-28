from odoo import models, fields
import logging

_logger = logging.getLogger(__name__)


class MigrationWizard(models.TransientModel):
    """Data Migration Wizard.

    Main wizard for migrating records between two Odoo 18.0 instances
    via JSON-RPC. The import cycle is orchestrated on the frontend (Owl 2).
    """

    _name = 'vd.migration.wizard'
    _description = 'Data Migration Wizard'

    # ── Source connection ─────────────────────────────────────────────
    source_url = fields.Char(
        string='Source URL',
        help='Base URL of the source Odoo instance (e.g. https://source.example.com).',
    )
    source_db = fields.Char(
        string='Database',
        help='Database name on the source Odoo instance.',
    )
    source_login = fields.Char(
        string='Login',
        help='Username for authentication on the source instance.',
    )
    source_password = fields.Char(
        string='Password',
        help='Password for authentication on the source instance.',
        password=True,
    )
    source_session_id = fields.Char(
        string='Session ID',
        help='JSON-RPC session_id obtained after authentication. Stored in memory only.',
    )

    # ── Target model & counters ───────────────────────────────────────
    target_model_id = fields.Many2one(
        comodel_name='ir.model',
        string='Target Model',
        help='Model in the current database to migrate records into.',
    )
    record_count_source = fields.Integer(
        string='Records in Source',
        help='Total number of records found in the source instance.',
        readonly=True,
    )
    record_count_target = fields.Integer(
        string='Records in Target',
        help='Total number of records currently in the target model.',
        readonly=True,
    )

    # ── Field mapping ─────────────────────────────────────────────────
    field_line_ids = fields.One2many(
        comodel_name='vd.migration.field.line',
        inverse_name='wizard_id',
        string='Field Mapping',
        help='List of fields to include or exclude from the migration.',
    )

    # ── Import control ────────────────────────────────────────────────
    start_batch_number = fields.Integer(
        string='Start Batch Number',
        help=(
            'Batch number to start from (1 = beginning). '
            'Each batch contains 100 records. '
            'Use this to resume a stopped migration.'
        ),
        default=1,
    )

    # ── Progress ──────────────────────────────────────────────────────
    progress = fields.Integer(
        string='Progress',
        help='Import progress in percent (0–100). Updated by the Owl component.',
        default=0,
    )
    progress_label = fields.Char(
        string='Progress Label',
        help='Human-readable progress label, e.g. "150 / 500 records".',
    )

    # ── Statistics ────────────────────────────────────────────────────
    stats_created = fields.Integer(
        string='Created',
        help='Number of records created during the last import run.',
        default=0,
    )
    stats_updated = fields.Integer(
        string='Updated',
        help='Number of records updated during the last import run.',
        default=0,
    )
    stats_errors = fields.Integer(
        string='Errors',
        help='Number of records that failed during the last import run.',
        default=0,
    )

    # ── State ─────────────────────────────────────────────────────────
    state = fields.Selection(
        selection=[
            ('draft',     'Draft'),
            ('analysed',  'Analysed'),
            ('loading',   'Loading'),
            ('done',      'Done'),
            ('stopped',   'Stopped'),
        ],
        string='State',
        help='Current state of the migration wizard.',
        default='draft',
    )

    # ── Actions (implemented in M4) ───────────────────────────────────

    def action_analyse(self):
        """Analyse the source instance and populate field_line_ids.

        Connects to the source via JSON-RPC, fetches field metadata,
        and compares with the target model. Sets state to 'analysed'.
        Implemented in M4.
        """
        pass

    def action_import(self):
        """Start the import process.

        Resets statistics, sets state to 'loading', and returns a form
        reload action so the Owl component can start the import cycle.
        Implemented in M4.
        """
        pass

    def action_delete(self):
        """Delete all records in the target model.

        Shows a confirmation dialog, then calls unlink() on all records
        of the selected target model. Resets record_count_target to 0.
        Implemented in M4.
        """
        pass

    def _get_rpc_client(self):
        """Create and return a JsonRpcClient instance from wizard fields.

        Returns:
            JsonRpcClient: configured with source_url, source_db,
                           source_login, source_password.
        Implemented in M4.
        """
        pass
