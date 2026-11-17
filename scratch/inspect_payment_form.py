import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pwd = 'lOnohi_1989' + '$tm'
ssh.connect('167.172.158.168', username='root', password=pwd, timeout=20)
sftp = ssh.open_sftp()

remote_script = """
import sys
sys.path.insert(0, '/opt/odoo/odoo')
import odoo
from odoo import api, SUPERUSER_ID
from odoo.modules.registry import Registry

odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
with Registry('Hanouty').cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # Check account.payment form view definition
    views = env['ir.ui.view'].search([('model', '=', 'account.payment'), ('type', '=', 'form')])
    for v in views:
        print(f"View {v.id}: {v.name} (xml_id={v.xml_id})")
        
    # Check default get for account.payment in different companies
    for comp in env['res.company'].search([]):
        print(f"\\n--- Company: {comp.name} (id={comp.id}) ---")
        # Inbound payment (client)
        pay_vals = env['account.payment'].with_company(comp).default_get(['payment_type', 'partner_type', 'journal_id', 'payment_method_line_id', 'payment_mode'])
        print(f"  default_get inbound: {pay_vals}")
        
        # Check what journals are available for inbound payment in this company
        journals = env['account.journal'].with_company(comp).search([
            ('company_id', '=', comp.id),
            ('type', 'in', ('bank', 'cash')),
        ])
        print(f"  All bank/cash journals in comp:")
        for j in journals:
            print(f"    j id={j.id}, name={j.name}, code={j.code}, type={j.type}, def_acc={j.default_account_id.id if j.default_account_id else None}, inbound_lines={[l.name for l in j.inbound_payment_method_line_ids]}")
"""

with sftp.file('/tmp/inspect_payment_form.py', 'w') as f:
    f.write(remote_script)

stdin, stdout, stderr = ssh.exec_command('su - odoo -s /bin/bash -c "PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/inspect_payment_form.py"')
print(stdout.read().decode('utf-8'))
print(stderr.read().decode('utf-8'))

