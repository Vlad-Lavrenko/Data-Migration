from odoo import models, fields
import logging

_logger = logging.getLogger(__name__)


class MigrationFieldLine(models.TransientModel):
    """One row in the field mapping table.

    Represents one field of the target model with metadata about
    whether the field exists in the source instance and whether it
    should be included in the migration.
    """

    _name = 'vd.migration.field.line'
    _description = 'Migration Field Line'

    wizard_id = fields.Many2one(
        comodel_name='vd.migration.wizard',
        string='Wizard',
        help='Reference to the parent migration wizard.',
        ondelete='cascade',
    )
    field_name = fields.Char(
        string='Field Name',
        help='Technical name of the field (e.g. partner_id).',
    )
    field_label = fields.Char(
        string='Label',
        help='Human-readable label of the field.',
    )
    field_type = fields.Char(
        string='Type',
        help='Field type (char, integer, many2one, etc.).',
    )
    source_exists = fields.Boolean(
        string='Exists in Source',
        help='True if this field exists in the source Odoo instance.',
        readonly=True,
    )
    include = fields.Boolean(
        string='Include',
        help='Include this field in the migration.',
        default=True,
    )
    comodel = fields.Char(
        string='Related Model',
        help='Related model name for Many2one / Many2many / One2many fields.',
    )
