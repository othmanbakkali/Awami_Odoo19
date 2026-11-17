path = 'Etat_Vente_Journalier_facturé/report/account_z_report_pdf.xml'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

target1 = """                                            <tr t-if="data.get('prior_payments_total', 0) > 0.005" style="background-color: #fef3c7; border-top: 1px dashed #d7c4b1;">
                                                <td style="font-weight: 800; color: #78350f; font-size: 10pt;">+ Encaissements Créances Antérieures</td>
                                                <td style="text-align: right; font-weight: 900; color: #78350f; font-size: 11.5pt; white-space: nowrap;">
                                                    <t t-esc="data['prior_payments_total']" t-options='{"widget": "monetary", "display_currency": o.company_id.currency_id}'/>
                                                </td>
                                            </tr>"""

replacement1 = """                                            <tr t-if="data.get('prior_payments_total', 0) > 0.005" style="background-color: #fef3c7; border-top: 1px dashed #d7c4b1;">
                                                <td style="font-weight: 800; color: #78350f; font-size: 10pt;">
                                                    + Encaissements Créances Antérieures
                                                    <div t-if="data.get('prior_payments_summary')" style="font-size: 8pt; font-weight: 600; color: #854d0e; margin-top: 2px;">
                                                        <t t-foreach="data['prior_payments_summary']" t-as="ps">
                                                            <span style="margin-right: 8px;">• <t t-esc="ps['mode']"/>: <strong t-esc="ps['amount']" t-options='{"widget": "monetary", "display_currency": o.company_id.currency_id}'/></span>
                                                        </t>
                                                    </div>
                                                </td>
                                                <td style="text-align: right; font-weight: 900; color: #78350f; font-size: 11.5pt; white-space: nowrap; vertical-align: top;">
                                                    <t t-esc="data['prior_payments_total']" t-options='{"widget": "monetary", "display_currency": o.company_id.currency_id}'/>
                                                </td>
                                            </tr>"""

target2 = """                                <tfoot>
                                    <tr style="background-color: #faf6f0; border-top: 2px solid #854d0e;">
                                        <td colspan="5" style="text-align: right; font-weight: 900; font-size: 8.5pt; color: #854d0e; text-transform: uppercase; padding: 5px 6px;">
                                            TOTAL ENCAISSEMENTS FACTURES ANTÉRIEURES :
                                        </td>
                                        <td style="text-align: right; font-weight: 900; font-size: 9pt; color: #15803d; white-space: nowrap; padding: 5px 3px;">
                                            <t t-esc="data.get('prior_payments_total', 0.0)" t-options='{"widget": "monetary", "display_currency": o.company_id.currency_id}'/>
                                        </td>
                                    </tr>
                                </tfoot>"""

replacement2 = """                                <tfoot>
                                    <t t-foreach="data.get('prior_payments_summary', [])" t-as="ps">
                                        <tr style="background-color: #faf6f0; border-top: 1px solid #e7ded4;">
                                            <td colspan="5" style="text-align: right; font-weight: 800; font-size: 8.5pt; color: #543216; padding: 4px 6px;">
                                                <span t-attf-class="z-badge #{'z-badge-especes' if ps['mode'] == 'Espèces' else ('z-badge-virement' if ps['mode'] == 'Virement' else ('z-badge-cheque' if ps['mode'] == 'Chèque' else ('z-badge-effet' if ps['mode'] == 'Effet' else 'z-badge-autre')))}" style="margin-right: 5px;">
                                                    <t t-esc="ps['mode'].upper()"/>
                                                </span>
                                                TOTAL <t t-esc="ps['mode'].upper()"/> (FACTURES ANTÉRIEURES) :
                                            </td>
                                            <td style="text-align: right; font-weight: 900; font-size: 8.5pt; color: #15803d; white-space: nowrap; padding: 4px 3px;">
                                                <t t-esc="ps['amount']" t-options='{"widget": "monetary", "display_currency": o.company_id.currency_id}'/>
                                            </td>
                                        </tr>
                                    </t>
                                    <tr style="background-color: #f5ede3; border-top: 2px solid #854d0e;">
                                        <td colspan="5" style="text-align: right; font-weight: 900; font-size: 8.5pt; color: #854d0e; text-transform: uppercase; padding: 5px 6px;">
                                            TOTAL ENCAISSEMENTS FACTURES ANTÉRIEURES :
                                        </td>
                                        <td style="text-align: right; font-weight: 900; font-size: 9.5pt; color: #15803d; white-space: nowrap; padding: 5px 3px;">
                                            <t t-esc="data.get('prior_payments_total', 0.0)" t-options='{"widget": "monetary", "display_currency": o.company_id.currency_id}'/>
                                        </td>
                                    </tr>
                                </tfoot>"""

assert target1 in content, "target1 not found!"
content = content.replace(target1, replacement1)

assert target2 in content, "target2 not found!"
content = content.replace(target2, replacement2)

with open(path, 'w', encoding='utf-8', newline='\n') as f:
    f.write(content)

print("Updated account_z_report_pdf.xml successfully!")

