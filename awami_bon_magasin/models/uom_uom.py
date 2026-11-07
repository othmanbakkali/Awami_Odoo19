# -*- coding: utf-8 -*-
import logging
from odoo import models, api

_logger = logging.getLogger(__name__)

class UoMUoM(models.Model):
    _inherit = 'uom.uom'

    def _register_hook(self):
        super()._register_hook()
        self._ensure_wood_uoms()

    @api.model
    def _ensure_wood_uoms(self):
        """Garantit que toutes les unités ml jusqu'à 7.0 ml existent dans Odoo 19"""
        try:
            self.env.cr.execute("SELECT 1 FROM information_schema.tables WHERE table_name = 'uom_uom'")
            if not self.env.cr.fetchone():
                return

            ref_ml = self.env.ref('uom.product_uom_milliliter', raise_if_not_found=False)
            if not ref_ml:
                ref_ml = self.search([('name', '=', 'ml')], limit=1)
            if not ref_ml:
                return

            # Valeurs souhaitées de 0.5 ml à 7.0 ml
            vals = set()
            for i in range(5, 71):
                vals.add(round(i * 0.1, 1))
            for i in range(1, 7):
                vals.add(round(i + 0.25, 2))
                vals.add(round(i + 0.75, 2))

            for val in sorted(vals):
                name = f"{val:.1f} ml" if val == round(val, 1) else f"{val:.2f} ml"
                comma_name = f"{str(val).replace('.', ',')} ml"
                existing = self.search([
                    '|',
                    ('name', '=', name),
                    ('name', '=', comma_name)
                ], limit=1)
                if not existing:
                    self.create({
                        'name': name,
                        'relative_factor': val,
                        'relative_uom_id': ref_ml.id,
                        'active': True,
                    })
        except Exception as e:
            _logger.warning("Could not auto-generate wood UoMs: %s", e)
