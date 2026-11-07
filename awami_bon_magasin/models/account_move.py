# -*- coding: utf-8 -*-
import re
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class AccountMove(models.Model):
    _inherit = 'account.move'

    payment_mode = fields.Selection([
        ('virement', 'Virement bancaire'),
        ('cheque', 'Chèque'),
        ('effet', 'Effet'),
        ('traite', 'Effet / Traite'),
        ('effet_cheque', 'Effet / Chèque'),
        ('especes', 'Espèces'),
    ], string="Mode de règlement", default='virement', tracking=True)

    check_number = fields.Char(
        string="N° de série / Chèque / Effet",
        tracking=True,
        copy=False,
        help="Numéro de série du chèque ou de l'effet commercial (Traite/LCN)."
    )

    check_client_name = fields.Char(
        string="Nom du client (Chèque / Effet)",
        tracking=True,
        copy=False,
        help="Nom du client ou titulaire figurant sur le chèque ou l'effet."
    )

    check_date_due = fields.Date(
        string="Date d'échéance",
        tracking=True,
        copy=False,
        help="Date d'échéance de l'effet ou date d'encaissement prévue du chèque."
    )

    @api.onchange('partner_id')
    def _onchange_partner_id_check_client(self):
        if self.partner_id and not self.check_client_name:
            self.check_client_name = self.partner_id.name

    @api.onchange('payment_mode')
    def _onchange_payment_mode_check(self):
        if self.payment_mode in ('cheque', 'effet', 'traite', 'effet_cheque'):
            if self.partner_id and not self.check_client_name:
                self.check_client_name = self.partner_id.name

    # Les informations de chèque / effet sont désormais saisies au niveau du Paiement et non sur la facture


    amount_total_words = fields.Char(
        string="Montant en lettres",
        compute='_compute_amount_total_words',
        help="Montant total en toutes lettres"
    )

    @api.depends('amount_total', 'currency_id')
    def _compute_amount_total_words(self):
        for move in self:
            if move.currency_id:
                try:
                    move.amount_total_words = move.currency_id.amount_to_text(move.amount_total)
                except Exception:
                    move.amount_total_words = ''
            else:
                move.amount_total_words = ''

    def _format_date_for_report(self, date_val):
        if not date_val:
            return ''
        if hasattr(date_val, 'strftime'):
            return date_val.strftime('%d/%m/%Y')
        if isinstance(date_val, str):
            try:
                dt = fields.Date.from_string(date_val)
                if dt:
                    return dt.strftime('%d/%m/%Y')
            except Exception:
                pass
            return str(date_val)
        return str(date_val)

    def _get_effective_payment_mode(self):
        """Retourne le mode de règlement réel issu des paiements ou de la facture."""
        self.ensure_one()
        for pay in self.matched_payment_ids | self.reconciled_payment_ids:
            if getattr(pay, 'payment_mode', False):
                return pay.payment_mode
        return self.payment_mode or 'virement'

    def _get_effective_check_number(self):
        """Retourne le numéro de chèque/effet issu du paiement ou de la facture."""
        self.ensure_one()
        if self.check_number:
            return self.check_number
        for pay in self.matched_payment_ids | self.reconciled_payment_ids:
            if getattr(pay, 'check_number', False):
                return pay.check_number
        return ''

    def _get_effective_check_client_name(self):
        """Retourne le nom de l'émetteur du chèque/effet."""
        self.ensure_one()
        if self.check_client_name:
            return self.check_client_name
        for pay in self.matched_payment_ids | self.reconciled_payment_ids:
            if getattr(pay, 'check_client_name', False):
                return pay.check_client_name
        return self.partner_id.name if self.partner_id else ''

    def _get_effective_check_date_due(self):
        """Retourne la date d'échéance du chèque/effet."""
        self.ensure_one()
        if self.check_date_due:
            return self.check_date_due
        for pay in self.matched_payment_ids | self.reconciled_payment_ids:
            if getattr(pay, 'check_date_due', False):
                return pay.check_date_due
        return False

    def _get_report_payment_lines(self):
        """Retourne la liste des règlements / modes de paiement avec leur montant pour l'affichage sous le montant total"""
        self.ensure_one()
        payments = []
        widget_data = self.invoice_payments_widget
        if widget_data:
            import json
            if isinstance(widget_data, (bytes, bytearray)):
                try:
                    widget_data = widget_data.decode('utf-8')
                except Exception:
                    widget_data = {}
            if isinstance(widget_data, str):
                try:
                    widget_data = json.loads(widget_data)
                except Exception:
                    widget_data = {}
            if isinstance(widget_data, dict) and widget_data.get('content'):
                for p in widget_data['content']:
                    pid = p.get('account_payment_id')
                    pay = self.env['account.payment'].browse(pid) if pid else False
                    
                    if pay and pay.exists():
                        mode_label = dict(pay._fields['payment_mode'].selection).get(pay.payment_mode) or pay.payment_method_line_id.name or p.get('journal_name') or 'Règlement'
                        details = []
                        if pay.check_number:
                            details.append(f"N° {pay.check_number}")
                        if pay.check_client_name and pay.check_client_name != self.partner_id.name:
                            details.append(f"Émetteur: {pay.check_client_name}")
                        if pay.check_date_due:
                            dt_str = self._format_date_for_report(pay.check_date_due)
                            if dt_str:
                                details.append(f"Éch: {dt_str}")
                        if details:
                            mode_label = f"{mode_label} ({', '.join(details)})"
                    else:
                        eff_mode = self._get_effective_payment_mode()
                        mode_label = p.get('journal_name') or dict(self._fields['payment_mode'].selection).get(eff_mode, 'Règlement')

                    payments.append({
                        'name': mode_label,
                        'amount': p.get('amount', 0.0),
                        'date': self._format_date_for_report(p.get('date')),
                    })

        if not payments and self.payment_mode:
            eff_mode = self._get_effective_payment_mode()
            mode_label = dict(self._fields['payment_mode'].selection).get(eff_mode, 'Paiement')
            details = []
            check_num = self._get_effective_check_number()
            check_client = self._get_effective_check_client_name()
            check_due = self._get_effective_check_date_due()
            if check_num:
                details.append(f"N° {check_num}")
            if check_client and check_client != self.partner_id.name:
                details.append(f"Émetteur: {check_client}")
            if check_due:
                dt_str = self._format_date_for_report(check_due)
                if dt_str:
                    details.append(f"Éch: {dt_str}")
            if details:
                mode_label = f"{mode_label} ({', '.join(details)})"

            if self.payment_state in ('paid', 'in_payment') or (self.state == 'posted' and self.amount_residual == 0):
                paid_amount = self.amount_total
            elif self.payment_state == 'partial':
                paid_amount = (self.amount_total or 0.0) - (self.amount_residual or 0.0)
            else:
                paid_amount = self.amount_total

            payments.append({
                'name': mode_label,
                'amount': paid_amount,
                'date': self._format_date_for_report(self.invoice_date),
            })

        return payments

    manual_amount_total = fields.Monetary(
        string="Montant Total Souhaité",
        currency_field='currency_id',
        copy=False,
        tracking=True,
        help="Saisissez ici le montant total TTC souhaité pour la facture. Le système ajoutera ou ajustera automatiquement une ligne de remise/ajustement."
    )

    @api.onchange('manual_amount_total')
    def _onchange_manual_amount_total(self):
        if self.state == 'draft':
            self._apply_manual_amount_total()

    def action_apply_manual_amount_total(self):
        for move in self:
            if move.state == 'draft':
                move._apply_manual_amount_total()

    def _apply_manual_amount_total(self):
        self.ensure_one()
        if not self.manual_amount_total or self.manual_amount_total <= 0:
            adj_lines = self.invoice_line_ids.filtered(lambda l: l.is_adjustment_line)
            if adj_lines:
                self.invoice_line_ids -= adj_lines
            return

        non_adj_lines = self.invoice_line_ids.filtered(lambda l: not l.is_adjustment_line and (not l.display_type or l.display_type == 'product'))
        if not non_adj_lines:
            return

        current_total = sum(l.price_total for l in non_adj_lines)
        diff_total = self.manual_amount_total - current_total

        if abs(diff_total) < 0.005:
            adj_lines = self.invoice_line_ids.filtered(lambda l: l.is_adjustment_line)
            if adj_lines:
                self.invoice_line_ids -= adj_lines
            return

        taxes = non_adj_lines[:1].tax_ids if non_adj_lines else False
        if taxes:
            res = taxes.compute_all(diff_total, currency=self.currency_id, quantity=1.0, is_refund=self.move_type == 'out_refund', handle_price_include=True)
            price_unit_net = res['total_excluded']
        else:
            price_unit_net = diff_total

        label = "Remise commerciale" if diff_total < 0 else "Ajustement global"
        account = non_adj_lines[0].account_id or self.journal_id.default_account_id
        existing_adj = self.invoice_line_ids.filtered(lambda l: l.is_adjustment_line)

        if existing_adj:
            existing_adj[:1].write({
                'name': label,
                'price_unit': price_unit_net,
                'tax_ids': [fields.Command.set(taxes.ids)] if taxes else False,
            })
            if len(existing_adj) > 1:
                self.invoice_line_ids -= existing_adj[1:]
        else:
            new_line_vals = {
                'name': label,
                'quantity': 1.0,
                'price_unit': price_unit_net,
                'account_id': account.id if account else False,
                'tax_ids': [fields.Command.set(taxes.ids)] if taxes else False,
                'is_adjustment_line': True,
            }
            self.invoice_line_ids = [fields.Command.create(new_line_vals)]

    _sequence_daily_regex = (
        r'^(?P<prefix1>.*?)'
        r'(?P<year>((?<=\D)|(?<=^))((19|20|21)\d{2}|(\d{2}(?=\D))))'
        r'(?P<prefix2>\D*?)'
        r'(?P<month>(0[1-9]|1[0-2]))'
        r'(?P<prefix3>\D*?)'
        r'(?P<day>(0[1-9]|[12]\d|3[01]))'
        r'(?P<prefix4>\D+?)'
        r'(?P<seq>\d{0,9})'
        r'(?P<suffix>\D*?)$'
    )

    @api.model
    def _deduce_sequence_number_reset(self, name):
        match = re.match(self._sequence_daily_regex, name or '')
        if match:
            groupdict = match.groupdict()
            if all(groupdict.get(req) is not None for req in ['seq', 'day', 'month', 'year']):
                return 'day'
        return super()._deduce_sequence_number_reset(name)

    def _get_sequence_date_range(self, reset):
        if reset == 'day':
            ref_date = fields.Date.to_date(self[self._sequence_date_field])
            return (ref_date, ref_date, None, None)
        return super()._get_sequence_date_range(reset)

    def _get_sequence_format_param(self, previous):
        sequence_number_reset = self._deduce_sequence_number_reset(previous)
        if sequence_number_reset == 'day':
            regex = self._sequence_daily_regex
            format_values = re.match(regex, previous).groupdict()
            format_values['seq_length'] = len(format_values['seq'])
            format_values['year_length'] = len(format_values.get('year') or '')
            format_values['year_end_length'] = 0
            if not format_values.get('seq') and 'prefix1' in format_values and 'suffix' in format_values:
                format_values['prefix1'] = format_values['suffix']
                format_values['suffix'] = ''
            for field in ('seq', 'year', 'month', 'day', 'year_end'):
                format_values[field] = int(format_values.get(field) or 0)

            placeholders = re.findall(r'\b(prefix\d|seq|suffix\d?|year|year_end|month|day)\b', regex)
            fmt = ''.join(
                "{seq:0{seq_length}d}" if s == 'seq' else
                "{day:02d}" if s == 'day' else
                "{month:02d}" if s == 'month' else
                "{year:0{year_length}d}" if s == 'year' else
                "{%s}" % s
                for s in placeholders
            )
            return fmt, format_values
        return super()._get_sequence_format_param(previous)

    def _get_next_sequence_format(self):
        format_string, format_values = super()._get_next_sequence_format()
        if 'day' in format_values and self[self._sequence_date_field]:
            move_date = fields.Date.to_date(self[self._sequence_date_field])
            format_values['day'] = move_date.day
            format_values['month'] = move_date.month
            format_values['year'] = move_date.year
            format_values['year_end'] = 0
        return format_string, format_values

    def _get_starting_sequence(self):
        self.ensure_one()
        if self.journal_id.type == 'sale' or self.move_type in ('out_invoice', 'out_refund'):
            move_date = self.date or self.invoice_date or fields.Date.context_today(self)
            return f"BL/{move_date.year:04d}/{move_date.month:02d}/{move_date.day:02d}/0000"
        return super()._get_starting_sequence()

    def _sequence_matches_date(self):
        date_val = fields.Date.to_date(self[self._sequence_date_field])
        sequence = self[self._sequence_field]
        if not sequence or not date_val:
            return True
        reset = self._deduce_sequence_number_reset(sequence)
        if reset == 'day':
            format_values = self._get_sequence_format_param(sequence)[1]
            year_match = not format_values['year'] or format_values['year'] == date_val.year
            month_match = not format_values['month'] or format_values['month'] == date_val.month
            day_match = not format_values.get('day') or format_values['day'] == date_val.day
            return year_match and month_match and day_match
        return super()._sequence_matches_date()

    def _get_last_sequence_domain(self, relaxed=False):
        where_string, param = super()._get_last_sequence_domain(relaxed=relaxed)
        if self.journal_id.type == 'sale' or self.move_type in ('out_invoice', 'out_refund'):
            where_string += " AND (sequence_prefix LIKE %(bl_pref)s OR sequence_prefix LIKE %(rbl_pref)s) "
            param['bl_pref'] = 'BL/%'
            param['rbl_pref'] = 'RBL/%'
        return where_string, param


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    product_uom_id = fields.Many2one(
        comodel_name='uom.uom',
        string='Unit',
        domain="[]",
        compute='_compute_product_uom_id',
        store=True,
        readonly=False,
        precompute=True,
        ondelete="restrict",
    )

    # Colonne Prix Unitaire de Base sur Facture (modifiable librement par l'utilisateur)
    base_price_unit = fields.Float(
        string="P.U Base",
        digits='Product Price',
        compute='_compute_base_price_unit',
        store=True,
        readonly=False,
        precompute=True,
        copy=True,
        help="Prix unitaire de référence (ex: prix au ml ou prix au m³). Utilisé comme base pour tous les calculs."
    )

    # Sauvegarde du prix unitaire manuel personnalisé
    custom_price_unit = fields.Float(string="Prix Unitaire Manuel", digits='Product Price', copy=True)

    is_adjustment_line = fields.Boolean(string="Ligne d'ajustement / remise", default=False, copy=False)

    # Champs dimensionnels pour les articles en mètre cube (m3) ou débit bois
    is_m3 = fields.Boolean(string="Article en m³", compute="_compute_is_m3", store=True)
    wood_length = fields.Float(string="Long. (m)", digits=(12, 5), default=0.0)
    wood_width = fields.Float(string="Larg. (m)", digits=(12, 5), default=0.0)
    wood_thickness = fields.Float(string="Épais. (m)", digits=(12, 5), default=0.0)
    wood_pieces = fields.Float(string="Nb Pièces", digits=(12, 0), default=1.0)
    volume_m3 = fields.Float(string="Vol. (m³)", digits=(12, 5), compute="_compute_volume_m3", store=True)

    @api.depends('product_id', 'product_uom_id')
    def _compute_is_m3(self):
        for line in self:
            if line.is_adjustment_line:
                line.is_m3 = False
                continue
            uom_name = (line.product_uom_id.name or line.product_id.uom_id.name or '').lower()
            prod_name = (line.product_id.name or '').lower()
            line.is_m3 = ('m³' in uom_name or 'm3' in uom_name or 'cube' in uom_name or 'm³' in prod_name or 'm3' in prod_name)

    @api.depends('product_id', 'sale_line_ids')
    def _compute_base_price_unit(self):
        """Calculer ou initialiser le prix unitaire de base de la facture"""
        for line in self:
            if line.is_adjustment_line:
                line.base_price_unit = line.price_unit
                continue
            if not line.product_id or line.display_type in ('line_section', 'line_subsection', 'line_note'):
                line.base_price_unit = 0.0
            elif line.sale_line_ids and line.sale_line_ids[:1].base_price_unit:
                line.base_price_unit = line.sale_line_ids[:1].base_price_unit
            elif not line.base_price_unit:
                line.base_price_unit = line.product_id.lst_price

    def _get_uom_ratio(self, base_uom, target_uom):
        """Calculer le ratio multiplicateur entre l'unité de base et l'unité choisie (ex: 4.2 ml -> 4.2)"""
        if not base_uom or not target_uom or base_uom == target_uom:
            return 1.0
        try:
            return base_uom._compute_price(1.0, to_unit=target_uom)
        except Exception:
            pass
        if hasattr(target_uom, 'factor') and hasattr(base_uom, 'factor') and base_uom.factor:
            return target_uom.factor / base_uom.factor
        if hasattr(target_uom, 'relative_factor'):
            return target_uom.relative_factor
        return 1.0

    @api.depends('base_price_unit', 'product_uom_id')
    def _compute_price_unit(self):
        """Prendre en compte le Prix Unitaire de Base dans le calcul du prix unitaire de facture"""
        super()._compute_price_unit()
        for line in self:
            if line.is_adjustment_line or line.display_type in ('line_section', 'line_subsection', 'line_note') or not line.product_id:
                continue
            if line.base_price_unit:
                base_uom = line.product_id.uom_id
                if line.is_m3 or line.wood_length:
                    line.price_unit = line.base_price_unit
                elif base_uom and line.product_uom_id:
                    ratio = line._get_uom_ratio(base_uom, line.product_uom_id)
                    line.price_unit = line.base_price_unit * ratio
                else:
                    line.price_unit = line.base_price_unit
                line.custom_price_unit = line.price_unit
            elif line.custom_price_unit:
                line.price_unit = line.custom_price_unit

    @api.onchange('product_id')
    def _onchange_product_id_set_base_price(self):
        """Initialiser le prix unitaire de base lors du choix de l'article sur la facture"""
        for line in self:
            if line.product_id:
                base_price = line.product_id.lst_price
                line.base_price_unit = base_price
                base_uom = line.product_id.uom_id
                if line.is_m3 or line.wood_length:
                    line.price_unit = base_price
                elif base_uom and line.product_uom_id:
                    ratio = line._get_uom_ratio(base_uom, line.product_uom_id)
                    line.price_unit = base_price * ratio
                else:
                    line.price_unit = base_price
                line.custom_price_unit = line.price_unit

    @api.depends('wood_length', 'wood_width', 'wood_thickness')
    def _compute_volume_m3(self):
        for line in self:
            if line.wood_length and line.wood_width and line.wood_thickness:
                line.volume_m3 = round(line.wood_length * line.wood_width * line.wood_thickness, 5)
            else:
                line.volume_m3 = 0.0

    @api.onchange('base_price_unit')
    def _onchange_base_price_unit(self):
        """Prendre en compte le nouveau Prix Unitaire de Base dans les calculs de la facture"""
        for line in self:
            if line.base_price_unit is not False:
                base_uom = line.product_id.uom_id if line.product_id else False
                if line.is_m3 or line.wood_length:
                    line.price_unit = line.base_price_unit
                elif base_uom and line.product_uom_id:
                    ratio = line._get_uom_ratio(base_uom, line.product_uom_id)
                    line.price_unit = line.base_price_unit * ratio
                else:
                    line.price_unit = line.base_price_unit
                line.custom_price_unit = line.price_unit

    @api.onchange('price_unit')
    def _onchange_price_unit_manual(self):
        """Synchronisation bidirectionnelle si l'utilisateur modifie directement le prix unitaire"""
        for line in self:
            if line.price_unit is not False:
                line.custom_price_unit = line.price_unit
                base_uom = line.product_id.uom_id if line.product_id else False
                if line.is_m3 or line.wood_length:
                    line.base_price_unit = line.price_unit
                elif base_uom and line.product_uom_id:
                    ratio = line._get_uom_ratio(base_uom, line.product_uom_id)
                    if ratio:
                        line.base_price_unit = line.price_unit / ratio
                else:
                    line.base_price_unit = line.price_unit

    @api.onchange('wood_length', 'wood_width', 'wood_thickness')
    def _onchange_wood_dimensions(self):
        """Calcul automatique du volume en m3 avec le prix de base sur la facture"""
        for line in self:
            if line.wood_length and line.wood_width and line.wood_thickness:
                vol = round(line.wood_length * line.wood_width * line.wood_thickness, 5)
                line.volume_m3 = vol
                line.quantity = vol
                if line.base_price_unit:
                    line.price_unit = line.base_price_unit
                    line.custom_price_unit = line.base_price_unit

    @api.onchange('product_uom_id')
    def _onchange_product_uom_id_convert_price(self):
        """Recalcul du prix sur facture à partir du Prix Unitaire de Base lors du changement d'unité"""
        for line in self:
            if not line.product_id or not line.product_uom_id:
                continue
            base_uom = line.product_id.uom_id
            ref_price = line.base_price_unit or line.custom_price_unit or line.product_id.lst_price
            if line.is_m3 or line.wood_length:
                line.price_unit = ref_price
            elif base_uom and line.product_uom_id:
                ratio = line._get_uom_ratio(base_uom, line.product_uom_id)
                line.price_unit = ref_price * ratio
            else:
                line.price_unit = ref_price
            line.custom_price_unit = line.price_unit

    @api.depends('product_id')
    def _compute_product_uom_id(self):
        super(AccountMoveLine, self)._compute_product_uom_id()
        for line in self:
            if line.sale_line_ids:
                sol = line.sale_line_ids[:1]
                if sol.product_uom_id:
                    line.product_uom_id = sol.product_uom_id
                if sol.base_price_unit:
                    line.base_price_unit = sol.base_price_unit
                if sol.price_unit:
                    line.price_unit = sol.price_unit
                    line.custom_price_unit = sol.price_unit
                if sol.wood_length and sol.wood_width and sol.wood_thickness:
                    line.wood_length = sol.wood_length
                    line.wood_width = sol.wood_width
                    line.wood_thickness = sol.wood_thickness
                    line.wood_pieces = sol.wood_pieces
                    line.volume_m3 = sol.volume_m3
