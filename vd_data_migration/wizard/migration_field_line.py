from odoo import models, fields
import logging

_logger = logging.getLogger(__name__)


class MigrationFieldLine(models.TransientModel):
    """One row in the field mapping table.

    Each line represents one field of the target model, with metadata
    about whether it exists in the source instance and whether it
    should be included in the migration.

    Fields are added in M2 (wizard models).
    """

    _name = 'vd.migration.field.line'
    _description = 'Migration Field Line'
