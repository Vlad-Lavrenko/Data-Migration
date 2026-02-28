import logging

from .json_rpc_client import JsonRpcClient

_logger = logging.getLogger(__name__)


class FieldMapper:
    """Maps fields from the source Odoo instance to the local target model.

    Compares fields available on the source (via JSON-RPC fields_get) with
    fields registered on the local target model (via Odoo env), and builds
    a list of dicts ready to be written into wizard.field_line_ids.
    """

    def __init__(self, rpc: JsonRpcClient, env) -> None:
        """Initialize the mapper.

        Args:
            rpc: Authenticated JsonRpcClient instance.
            env: Odoo Environment (self.env from the wizard).
        """
        self._rpc = rpc
        self._env = env

    def build_field_lines(self, model_name: str) -> list[dict]:
        """Build field mapping lines for the given model.

        Steps:
            1. Fetch source fields via JSON-RPC (fields_get).
            2. Read target fields from local Odoo env.
            3. For each local field: set source_exists, include flag, comodel.
            4. one2many fields default to include=False (out of scope for v1).

        Args:
            model_name: Technical model name (e.g. 'res.partner').

        Returns:
            list[dict]: Dicts suitable for writing into field_line_ids.
        """
        source_fields = self._rpc.fields_get(model_name)
        target_model = self._env.get(model_name)

        if target_model is None:
            _logger.warning('build_field_lines: model %s not found in local env', model_name)
            return []

        local_fields = target_model._fields
        lines = []

        for field_name, field_obj in local_fields.items():
            field_type = field_obj.type
            comodel = getattr(field_obj, 'comodel_name', '') or ''
            source_exists = field_name in source_fields

            # one2many is excluded from migration by default (v1 scope, see requirements)
            include = field_type != 'one2many'

            lines.append({
                'field_name': field_name,
                'field_label': field_obj.string or field_name,
                'field_type': field_type,
                'source_exists': source_exists,
                'include': include,
                'comodel': comodel,
            })

        _logger.info(
            'build_field_lines(%s): %d lines (source: %d fields, local: %d fields)',
            model_name, len(lines), len(source_fields), len(local_fields),
        )
        return lines
