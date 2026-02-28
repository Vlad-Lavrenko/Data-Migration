import logging

from odoo import http
from odoo.http import request

from ..services.json_rpc_client import JsonRpcClient
from ..services.record_importer import RecordImporter

_logger = logging.getLogger(__name__)

BATCH_SIZE = 100  # NFR-04: exactly 100 records per batch


class MigrationController(http.Controller):
    """HTTP JSON endpoints for the Owl 2 import orchestrator.

    All routes:
        - method: POST
        - auth:   user
        - type:   json  (plain JSON body, not JSON-RPC wrapper)

    Errors always return { "error": "<message>" } so the frontend
    can surface them without raising unhandled exceptions.
    """

    # ── fetch_batch ─────────────────────────────────────────────────────

    @http.route(
        '/vd_migration/fetch_batch',
        type='json',
        auth='user',
        methods=['POST'],
        csrf=False,
    )
    def fetch_batch(
        self,
        wizard_id: int,
        offset: int,
        limit: int = BATCH_SIZE,
        **kwargs,
    ) -> dict:
        """Fetch a batch of records from the source Odoo instance.

        Reuses wizard.source_session_id to avoid re-authentication
        on every request. Only fetches fields with include=True and
        source_exists=True (FR-06, NFR-04).

        Args:
            wizard_id: ID of vd.migration.wizard.
            offset: Pagination offset.
            limit: Batch size (default 100).

        Returns:
            dict: { records: list[dict], total: int }
                  or { error: str } on failure.
        """
        wizard = self._get_wizard(wizard_id)
        if wizard is None:
            return {'error': f'Wizard {wizard_id} not found.'}

        model_name = wizard.target_model_id.model
        if not model_name:
            return {'error': 'No target model selected on wizard.'}

        # Only request fields that exist on the source and are included
        fields = [
            fl.field_name
            for fl in wizard.field_line_ids
            if fl.include and fl.source_exists
        ]
        if 'id' not in fields:
            fields = ['id'] + fields

        try:
            rpc = self._build_rpc_client(wizard)
            records = rpc.search_read(model_name, fields, offset, limit)
            _logger.info(
                'fetch_batch: wizard=%s model=%s offset=%d got=%d',
                wizard_id, model_name, offset, len(records),
            )
            return {'records': records, 'total': wizard.record_count_source}
        except Exception as exc:
            _logger.error('fetch_batch: wizard=%s error=%s', wizard_id, exc)
            return {'error': str(exc)}

    # ── process_record ───────────────────────────────────────────────

    @http.route(
        '/vd_migration/process_record',
        type='json',
        auth='user',
        methods=['POST'],
        csrf=False,
    )
    def process_record(
        self,
        wizard_id: int,
        record: dict,
        **kwargs,
    ) -> dict:
        """Process a single record: write or create it in the local database.

        Statistics are accumulated on the frontend and sent via /finalize,
        so this endpoint does not write stats to the wizard.

        Args:
            wizard_id: ID of vd.migration.wizard.
            record: Record dict from fetch_batch (search_read result).

        Returns:
            dict: { created: 0|1, updated: 0|1, errors: 0|1 }
                  or { error: str } on unexpected failure.
        """
        wizard = self._get_wizard(wizard_id)
        if wizard is None:
            return {'created': 0, 'updated': 0, 'errors': 1,
                    'error': f'Wizard {wizard_id} not found.'}

        model_name = wizard.target_model_id.model
        if not model_name:
            return {'created': 0, 'updated': 0, 'errors': 1,
                    'error': 'No target model on wizard.'}

        # Serialize One2many field lines to plain dicts for RecordImporter
        field_lines = wizard.field_line_ids.read([
            'field_name', 'field_type', 'include', 'comodel',
        ])

        try:
            importer = RecordImporter(request.env, wizard)
            result = importer.process_record(model_name, record, field_lines)
            _logger.debug(
                'process_record: wizard=%s id=%s result=%s',
                wizard_id, record.get('id'), result,
            )
            return result
        except Exception as exc:
            _logger.error('process_record: wizard=%s error=%s', wizard_id, exc)
            return {'created': 0, 'updated': 0, 'errors': 1, 'error': str(exc)}

    # ── finalize ────────────────────────────────────────────────────────

    @http.route(
        '/vd_migration/finalize',
        type='json',
        auth='user',
        methods=['POST'],
        csrf=False,
    )
    def finalize(
        self,
        wizard_id: int,
        state: str,
        stats: dict | None = None,
        **kwargs,
    ) -> dict:
        """Finalize the import: persist final state and statistics.

        Called by the Owl component after the import loop ends
        (both for 'done' and 'stopped' states, FR-06 / FR-10).

        Args:
            wizard_id: ID of vd.migration.wizard.
            state: Final state — 'done' or 'stopped'.
            stats: Dict { created, updated, errors } accumulated by frontend.

        Returns:
            dict: { ok: True } or { ok: False, error: str }
        """
        wizard = self._get_wizard(wizard_id)
        if wizard is None:
            return {'ok': False, 'error': f'Wizard {wizard_id} not found.'}

        # Guard against unexpected state values
        if state not in ('done', 'stopped'):
            _logger.warning('finalize: unexpected state=%s, defaulting to done', state)
            state = 'done'

        vals: dict = {'state': state}
        if stats:
            vals['stats_created'] = int(stats.get('created', 0))
            vals['stats_updated'] = int(stats.get('updated', 0))
            vals['stats_errors']  = int(stats.get('errors',  0))

        # sudo: writing progress fields after frontend-driven import
        wizard.sudo().write(vals)  # sudo: update wizard state and stats post-import

        _logger.info(
            'finalize: wizard=%s state=%s stats=%s', wizard_id, state, stats,
        )
        return {'ok': True}

    # ── stop ─────────────────────────────────────────────────────────────

    @http.route(
        '/vd_migration/stop/<int:wizard_id>',
        type='json',
        auth='user',
        methods=['POST'],
        csrf=False,
    )
    def stop(self, wizard_id: int, **kwargs) -> dict:
        """Backend-side emergency stop: set wizard state to 'stopped'.

        The primary stop mechanism is the frontend flag this._stopped (FR-10).
        This endpoint provides a server-side safety stop (e.g. tab close).

        Args:
            wizard_id: ID of vd.migration.wizard.

        Returns:
            dict: { ok: True } or { ok: False, error: str }
        """
        wizard = self._get_wizard(wizard_id)
        if wizard is None:
            return {'ok': False, 'error': f'Wizard {wizard_id} not found.'}

        wizard.sudo().write({'state': 'stopped'})  # sudo: emergency stop from frontend
        _logger.info('stop: wizard=%s forced to stopped', wizard_id)
        return {'ok': True}

    # ── Private helpers ───────────────────────────────────────────────

    @staticmethod
    def _get_wizard(wizard_id: int):
        """Fetch the wizard record from the current environment.

        Returns:
            vd.migration.wizard recordset, or None if not found.
        """
        wizard = request.env['vd.migration.wizard'].browse(wizard_id)
        return wizard if wizard.exists() else None

    @staticmethod
    def _build_rpc_client(wizard) -> JsonRpcClient:
        """Create a JsonRpcClient reusing the stored session_id.

        Avoids re-authentication on every fetch_batch request during
        the import loop. The session was established by action_analyse().

        Args:
            wizard: vd.migration.wizard recordset.

        Returns:
            JsonRpcClient: Pre-authenticated client.
        """
        rpc = JsonRpcClient(
            url=wizard.source_url,
            db=wizard.source_db,
            login=wizard.source_login,
            password=wizard.source_password,
        )
        # Restore the session from wizard field (no re-authentication needed)
        rpc._session_id = wizard.source_session_id
        rpc._uid = 1  # uid is not used by _call_kw
        return rpc
