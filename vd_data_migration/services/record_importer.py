import logging

_logger = logging.getLogger(__name__)


class RecordImporter:
    """Handles per-record import from source data into the local Odoo database.

    The import loop (batches + per-record iteration) is driven by the frontend
    (Owl 2 MigrationProgressWidget). This class processes one record at a time:
    prepares field values, finds or creates the local record, and returns a
    result dict for the frontend to accumulate statistics.
    """

    def __init__(self, env, wizard) -> None:
        """Initialize the importer.

        Args:
            env: Odoo Environment.
            wizard: vd.migration.wizard recordset.
        """
        self._env = env
        self._wizard = wizard

    def process_record(
        self,
        model_name: str,
        record: dict,
        field_lines: list,
    ) -> dict:
        """Process a single record: write or create it in the local database.

        Args:
            model_name: Technical model name (e.g. 'res.partner').
            record: Dict of field values from the source (search_read result).
            field_lines: List of field line dicts from wizard.field_line_ids.

        Returns:
            dict: {'created': 0|1, 'updated': 0|1, 'errors': 0|1}
        """
        source_id = record.get('id')
        try:
            values = self._prepare_values(record, field_lines)
            local_id = self._find_local_record(model_name, source_id)

            if local_id:
                self._env[model_name].browse(local_id).write(values)
                _logger.debug('Record %s/%s: updated', model_name, source_id)
                return {'created': 0, 'updated': 1, 'errors': 0}
            else:
                self._env[model_name].create(values)
                _logger.debug('Record %s/%s: created', model_name, source_id)
                return {'created': 1, 'updated': 0, 'errors': 0}

        except Exception as exc:
            _logger.error('Record %s/%s: error — %s', model_name, source_id, exc)
            return {'created': 0, 'updated': 0, 'errors': 1}

    def _prepare_values(self, record: dict, field_lines: list) -> dict:
        """Convert a source record dict into values suitable for write/create.

        Transformation rules per field type:
          - many2one  → _resolve_many2one()
          - many2many → _resolve_many2many()
          - one2many  → always skipped
          - include=False → skipped
          - all other types → copied as-is

        Args:
            record: Raw record dict from source search_read.
            field_lines: List of field line dicts with include/type/comodel info.

        Returns:
            dict: Values dict ready for ORM write/create.
        """
        values = {}
        line_map = {fl['field_name']: fl for fl in field_lines}

        for field_name, raw_value in record.items():
            if field_name == 'id':
                continue

            line = line_map.get(field_name)
            if not line or not line.get('include'):
                continue

            field_type = line.get('field_type', '')
            comodel = line.get('comodel', '')

            if field_type == 'many2one':
                # search_read returns [id, display_name] or False
                if isinstance(raw_value, (list, tuple)) and raw_value:
                    values[field_name] = self._resolve_many2one(comodel, raw_value[0])
                elif raw_value:
                    values[field_name] = self._resolve_many2one(comodel, raw_value)
                else:
                    values[field_name] = False

            elif field_type == 'many2many':
                ids = raw_value if isinstance(raw_value, list) else []
                values[field_name] = self._resolve_many2many(comodel, ids)

            elif field_type == 'one2many':
                # one2many is out of scope for v1 — always skip
                continue

            else:
                values[field_name] = raw_value

        return values

    def _find_local_record(self, model_name: str, source_id: int) -> int | None:
        """Search for an existing local record by source id.

        Args:
            model_name: Technical model name.
            source_id: The id value from the source instance.

        Returns:
            int | None: Local record id if found, None otherwise.
        """
        result = self._env[model_name].search([('id', '=', source_id)], limit=1)
        return result.id if result else None

    def _resolve_many2one(self, comodel: str, source_id: int) -> int | bool:
        """Resolve a many2one source id to a local record id (FR-08).

        Searches for a local record with matching id.
        If not found, creates a placeholder with name='<{source_id}>'.

        Args:
            comodel: Related model name.
            source_id: The id from the source instance.

        Returns:
            int | False: Local record id, or False if resolution failed.
        """
        if not comodel or not source_id:
            return False

        local = self._env[comodel].search([('id', '=', source_id)], limit=1)
        if local:
            _logger.debug('_resolve_many2one %s/%s: found local', comodel, source_id)
            return local.id

        # Create a placeholder record
        vals = {}
        if 'name' in self._env[comodel]._fields:
            vals['name'] = f'<{source_id}>'

        try:
            created = self._env[comodel].create(vals)
            _logger.debug(
                '_resolve_many2one %s/%s: created placeholder id=%s',
                comodel, source_id, created.id,
            )
            return created.id
        except Exception as exc:
            _logger.error(
                '_resolve_many2one %s/%s: failed to create placeholder: %s',
                comodel, source_id, exc,
            )
            return False

    def _resolve_many2many(self, comodel: str, source_ids: list) -> list:
        """Resolve a list of many2many source ids to local ids (FR-09).

        Applies _resolve_many2one for each id in source_ids.

        Args:
            comodel: Related model name.
            source_ids: List of ids from the source instance.

        Returns:
            list: ORM replace command [(6, 0, [local_id1, ...])].
        """
        local_ids = []
        for source_id in source_ids:
            local_id = self._resolve_many2one(comodel, source_id)
            if local_id:
                local_ids.append(local_id)
        return [(6, 0, local_ids)]
