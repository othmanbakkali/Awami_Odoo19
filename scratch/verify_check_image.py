import paramiko

HOST = "167.172.158.168"
USER = "root"
PASSWORD = "lOnohi_1989" + "$tm"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD, timeout=30)

verify_script = """
import odoo
from odoo.modules.registry import Registry
from odoo import api, SUPERUSER_ID

odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
reg = Registry('Hanouty')

with reg.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    partner = env['res.partner'].search([], limit=1)
    journal = env['account.journal'].search([('name', 'ilike', 'chèque')], limit=1)
    if not journal:
        journal = env['account.journal'].search([('type', '=', 'bank')], limit=1)
        
    company = journal.company_id
    env = env(context=dict(env.context, allowed_company_ids=[company.id]))

    dummy_img = b"R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
    
    payment = env['account.payment'].create({
        'company_id': company.id,
        'partner_id': partner.id,
        'amount': 500.0,
        'payment_type': 'inbound',
        'partner_type': 'customer',
        'journal_id': journal.id,
        'payment_mode': 'cheque',
        'check_number': 'TEST-CHQ-PHOTO-001',
        'check_client_name': partner.name,
        'check_image': dummy_img,
    })
    
    print("Created payment ID:", payment.id, "has check_image:", bool(payment.check_image))
    
    suivi = env['suivi.cheque'].search([('payment_id', '=', payment.id)], limit=1)
    if suivi:
        print("Suivi ID:", suivi.id, "has check_image:", bool(suivi.check_image))
        print("Suivi check_number:", suivi.check_number, "mode:", suivi.payment_mode)
    else:
        print("Suivi NOT found!")
        
    payment.unlink()
    if suivi:
        suivi.unlink()
    print("VERIFICATION SUCCESS: All checks passed and test data cleaned up.")
"""

sftp = ssh.open_sftp()
with sftp.file("/tmp/verify_check_image.py", "w") as f:
    f.write(verify_script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command(
    "su - odoo -s /bin/bash -c 'PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/verify_check_image.py'",
    timeout=60
)
print("STDOUT:\n", stdout.read().decode('utf-8', errors='ignore'))
print("STDERR:\n", stderr.read().decode('utf-8', errors='ignore'))
ssh.close()
