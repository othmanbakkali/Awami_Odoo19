import paramiko
import os
import sys

HOST = "167.172.158.168"
USER = "root"
PASS = "lOnohi_1989" + "$tm"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASS, timeout=30)

sftp = ssh.open_sftp()

upload_pairs = [
    (r"C:\Projects\Awami OUssama\awami_bon_magasin\models\account_payment.py",
     "/opt/odoo/custom-addons/awami_bon_magasin/models/account_payment.py"),
    (r"C:\Projects\Awami OUssama\awami_bon_magasin\models\account_move.py",
     "/opt/odoo/custom-addons/awami_bon_magasin/models/account_move.py"),
    (r"C:\Projects\Awami OUssama\awami_bon_magasin\models\sale_order.py",
     "/opt/odoo/custom-addons/awami_bon_magasin/models/sale_order.py"),
    (r"C:\Projects\Awami OUssama\awami_bon_magasin\views\account_payment_views.xml",
     "/opt/odoo/custom-addons/awami_bon_magasin/views/account_payment_views.xml"),

    (r"C:\Projects\Awami OUssama\Etat_Vente_Journalier_facturé\models\account_z_report.py",
     "/opt/odoo/custom-addons/etat_vente_journalier_facture/models/account_z_report.py"),
    (r"C:\Projects\Awami OUssama\Etat_Vente_Journalier_facturé\report\account_z_report_pdf.xml",
     "/opt/odoo/custom-addons/etat_vente_journalier_facture/report/account_z_report_pdf.xml"),
    (r"C:\Projects\Awami OUssama\Etat_Vente_Journalier_facturé\models\account_z_report.py",
     "/opt/odoo/custom-addons/Etat_Vente_Journalier_facturé/models/account_z_report.py"),
    (r"C:\Projects\Awami OUssama\Etat_Vente_Journalier_facturé\report\account_z_report_pdf.xml",
     "/opt/odoo/custom-addons/Etat_Vente_Journalier_facturé/report/account_z_report_pdf.xml"),

    (r"C:\Projects\Awami OUssama\Report\models\account_sales_expense_report.py",
     "/opt/odoo/custom-addons/Report/models/account_sales_expense_report.py"),
    (r"C:\Projects\Awami OUssama\Report\report\report_sales_expense_pdf.xml",
     "/opt/odoo/custom-addons/Report/report/report_sales_expense_pdf.xml"),
]

for local, remote in upload_pairs:
    print(f"Uploading {local} -> {remote}")
    sftp.put(local, remote)

remote_script = """
import odoo
from odoo.modules.registry import Registry
from odoo import api, SUPERUSER_ID
from odoo.exceptions import UserError

odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
reg = Registry('Hanouty')

with reg.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # Upgrade modules
    for mod_name in ['awami_bon_magasin', 'etat_vente_journalier_facture', 'Report']:
        mod = env['ir.module.module'].search([('name', '=', mod_name)])
        if mod:
            print(f'Upgrading {mod_name}...')
            mod.button_immediate_upgrade()
    cr.commit()

# Test validation
with reg.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    comp = env['res.company'].search([], limit=1)
    partner = env['res.partner'].search([], limit=1)
    journal_bank = env['account.journal'].search([('company_id', '=', comp.id), ('type', '=', 'bank'), ('name', 'not ilike', 'chèque'), ('name', 'not ilike', 'effet')], limit=1)
    if not journal_bank:
        journal_bank = env['account.journal'].search([('company_id', '=', comp.id), ('type', '=', 'bank')], limit=1)

    print('Testing account.payment validation...')
    # Test 1: Virement without transfer_order_number should raise UserError on post
    pay1 = env['account.payment'].create({
        'payment_type': 'inbound',
        'partner_type': 'customer',
        'partner_id': partner.id,
        'amount': 500.0,
        'journal_id': journal_bank.id,
        'payment_mode': 'virement',
        'company_id': comp.id,
    })
    
    raised = False
    try:
        pay1.action_post()
    except UserError as e:
        raised = True
        print('SUCCESS: Caught expected UserError on virement without OV number:', e)
    
    if not raised:
        print('ERROR: Expected UserError but none was raised!')
    else:
        # Test 2: Provide transfer_order_number and post
        pay1.write({'transfer_order_number': 'OV-TEST-123456'})
        pay1.action_post()
        print('SUCCESS: pay1 posted cleanly with transfer_order_number! State:', pay1.state, 'check_number:', pay1.check_number)
        
        # Cleanup test payment
        pay1.action_draft()
        pay1.action_cancel()
        pay1.unlink()
        print('Cleaned up test payment.')
    cr.commit()
"""

with sftp.file("/tmp/run_test_virement_ov.py", "w") as f:
    f.write(remote_script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command(
    "su - odoo -s /bin/bash -c 'PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/run_test_virement_ov.py'",
    timeout=180
)
print("STDOUT:\n", stdout.read().decode('utf-8', errors='ignore'))
print("STDERR:\n", stderr.read().decode('utf-8', errors='ignore'))

# Restart odoo service
print("Restarting odoo...")
stdin, stdout, stderr = ssh.exec_command("systemctl restart odoo")
stdout.channel.recv_exit_status()

# Verify odoo is running
stdin, stdout, stderr = ssh.exec_command("systemctl is-active odoo")
print("Odoo active status:", stdout.read().decode('utf-8').strip())

ssh.close()
