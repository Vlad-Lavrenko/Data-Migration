from odoo import models, fields
import logging

_logger = logging.getLogger(__name__)


class MigrationWizard(models.TransientModel):
    """Data Migration Wizard.

    Main wizard model for migrating records between two Odoo 18.0
    instances via JSON-RPC.

    Fields and methods are added in M2 (wizard models) and M4 (actions).
    """

    _name = 'vd.migration.wizard'
    _description = 'Data Migration Wizard'
