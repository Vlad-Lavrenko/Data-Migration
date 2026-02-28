import logging

from odoo import models, fields
from odoo.exceptions import UserError

from ..services.json_rpc_client import JsonRpcClient
from ..services.field_mapper import FieldMapper

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

    # ── Public actions ─────────────────────────────────────────────────

    def action_analyse(self):
        """Analyse the source instance and populate field_line_ids.

        Steps (FR-05):
            1. Validate required fields.
            2. Authenticate via JSON-RPC and store session_id.
            3. Verify the target model exists on the source.
            4. Fetch record counts (source + local target).
            5. Build field mapping lines via FieldMapper.
            6. Write results to the wizard and set state='analysed'.

        Raises:
            UserError: On missing fields, unreachable server, or unknown model.
        """
        self.ensure_one()
        self._validate_connection_fields()

        rpc = self._get_rpc_client()
        model_name = self.target_model_id.model
        model_label = self.target_model_id.name

        # Verify model exists on source instance (FR-05, step 3)
        if not rpc.model_exists(model_name):
            raise UserError(
                f'Model "{model_label}" ({model_name}) '
                f'does not exist on the source instance.'
            )

        count_source = rpc.search_count(model_name)
        count_target = self.env[model_name].search_count([])

        mapper = FieldMapper(rpc, self.env)
        lines = mapper.build_field_lines(model_name)

        # (5,0,0) deletes all existing lines before writing new ones
        self.write({
            'record_count_source': count_source,
            'record_count_target': count_target,
            'field_line_ids': [(5, 0, 0)] + [(0, 0, line) for line in lines],
            'state': 'analysed',
        })

        _logger.info(
            'action_analyse: model=%s source=%d target=%d fields=%d',
            model_name, count_source, count_target, len(lines),
        )
        return True

    def action_import(self):
        """Start the import process (FR-06 backend part).

        Validates state, resets statistics, sets state='loading', and returns
        a form reload action so the Owl component detects the state change
        and starts the import cycle.

        Returns:
            dict: ir.actions.act_window that reopens this wizard record.

        Raises:
            UserError: If state is not 'analysed'.
        """
        self.ensure_one()
        if self.state != 'analysed':
            raise UserError('Run «Analyse» first before starting the import.')

        self.write({
            'stats_created':  0,
            'stats_updated':  0,
            'stats_errors':   0,
            'progress':       0,
            'progress_label': '',
            'state':          'loading',
        })

        _logger.info('action_import: wizard=%s state=loading', self.id)

        # Reload the form so the Owl widget detects state='loading'
        view_id = self.env.ref('vd_data_migration.view_vd_migration_wizard_form').id
        return {
            'type':      'ir.actions.act_window',
            'res_model': self._name,
            'res_id':    self.id,
            'view_mode': 'form',
            'target':    'new',
            'view_id':   view_id,
        }

    def action_delete(self):
        """Delete all records of the target model (FR-07).

        The XML button carries confirm="..." so the user already confirmed
        before this method is called. Deletes all records, resets
        record_count_target, and shows a success notification.

        Returns:
            dict: display_notification action with deletion summary.

        Raises:
            UserError: If no target model is selected.
        """
        self.ensure_one()
        if not self.target_model_id:
            raise UserError('Select a target model first.')

        model_name  = self.target_model_id.model
        model_label = self.target_model_id.name

        records = self.env[model_name].search([])
        count   = len(records)
        records.unlink()  # sudo: authorised by group_migration_admin (see security)

        self.write({'record_count_target': 0})

        _logger.info(
            'action_delete: model=%s deleted=%d records', model_name, count,
        )

        return {
            'type': 'ir.actions.client',
            'tag':  'display_notification',
            'params': {
                'title':   'Видалено',
                'message': f'Видалено {count} записів моделі «{model_label}».',
                'type':    'success',
                'sticky':  False,
            },
        }

    # ── Private helpers ───────────────────────────────────────────────

    def _get_rpc_client(self) -> JsonRpcClient:
        """Create, authenticate, and return a JsonRpcClient.

        Stores the session_id in source_session_id (TransientModel memory only).

        Returns:
            JsonRpcClient: Authenticated client ready for RPC calls.

        Raises:
            UserError: Propagated from JsonRpcClient.authenticate().
        """
        rpc = JsonRpcClient(
            url=self.source_url,
            db=self.source_db,
            login=self.source_login,
            password=self.source_password,
        )
        session_id = rpc.authenticate()
        self.source_session_id = session_id  # stored in TransientModel memory only
        return rpc

    def _validate_connection_fields(self) -> None:
        """Raise UserError if any required connection field is missing.

        Raises:
            UserError: With a list of missing field labels.
        """
        missing = []
        if not self.source_url:      missing.append('Source URL')
        if not self.source_db:       missing.append('Database')
        if not self.source_login:    missing.append('Login')
        if not self.source_password: missing.append('Password')
        if not self.target_model_id: missing.append('Target Model')
        if missing:
            raise UserError(f'Fill in required fields: {", ".join(missing)}.')
