import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pwd = 'lOnohi_1989' + '$tm'
ssh.connect('167.172.158.168', username='root', password=pwd, timeout=20)

sftp = ssh.open_sftp()
with open('awami_bon_magasin/models/account_payment.py', 'r', encoding='utf-8') as f:
    content = f.read()
with sftp.file('/opt/odoo/custom-addons/awami_bon_magasin/models/account_payment.py', 'w') as f:
    f.write(content)
sftp.close()
print("Uploaded account_payment.py")

stdin, stdout, stderr = ssh.exec_command("systemctl stop odoo")
stdout.read()

cmd = "su - odoo -s /bin/bash -c '/opt/odoo/odoo-venv/bin/python3 /opt/odoo/odoo/odoo-bin -c /etc/odoo.conf -d Hanouty -u awami_bon_magasin --stop-after-init'"
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=120)
out = stdout.read().decode('utf-8')
err = stderr.read().decode('utf-8')
if "ERROR" in err or "Traceback" in err:
    print("Upgrade STDERR:\n", err)
else:
    print("Upgrade successful!")

stdin, stdout, stderr = ssh.exec_command("systemctl start odoo")
stdout.read()
print("Odoo started.")

# Test register payment wizard on Move 1800 (Agence Awama)
test_script = r'''
import odoo
from odoo.modules.registry import Registry
from odoo import api, SUPERUSER_ID

odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
registry = Registry('Hanouty')
with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    m1800 = env['account.move'].browse(1800) # Agence Awama
    print(f"Testing invoice {m1800.name} (company={m1800.company_id.name}, payment_mode={m1800.payment_mode})")
    
    # 1. Wizard with default compute
    wiz = env['account.payment.register'].with_company(m1800.company_id.id).with_context(
        active_model='account.move', active_ids=[m1800.id]
    ).new()
    wiz._compute_journal_id()
    print(f"Default journal computed: {wiz.journal_id.name} (type={wiz.journal_id.type}, code={wiz.journal_id.code})")
    wiz._compute_payment_mode()
    print(f"Default payment_mode: {wiz.payment_mode}")
    
    # 2. Check available journals in wizard for Agence Awama
    available_journals = env['account.journal'].search([
        ('company_id', '=', m1800.company_id.id),
        ('type', 'in', ('bank', 'cash'))
    ])
    print(f"\nAvailable journals for {m1800.company_id.name}:")
    for j in available_journals:
        print(f"  - [{j.type.upper()}] {j.name} (code: {j.code})")
'''

sftp = ssh.open_sftp()
with sftp.file('/tmp/test_wiz_awama.py', 'w') as f:
    f.write(test_script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c 'PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/test_wiz_awama.py'")
print("Test STDOUT:\n", stdout.read().decode('utf-8'))
print("Test STDERR:\n", stderr.read().decode('utf-8'))
ssh.close()

