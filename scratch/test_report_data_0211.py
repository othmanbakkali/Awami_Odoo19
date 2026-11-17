import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pwd = 'lOnohi_1989' + '$tm'
ssh.connect('167.172.158.168', username='root', password=pwd, timeout=30)

test_script = """import sys
sys.path.insert(0, '/opt/odoo/odoo')
import odoo
from odoo import api, SUPERUSER_ID
from odoo.modules.registry import Registry

odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
with Registry('Hanouty').cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    c1 = env['res.company'].browse(1)
    
    # Check what account.z.report returns for 02/11/2026
    rep_z = env['account.z.report'].with_company(c1).new({
        'company_id': c1.id,
        'report_type': 'x',
        'date_start': '2026-11-02',
        'date_end': '2026-11-02',
    })
    data_z = rep_z.get_report_data()
    print("=== RAPPORT Z DATA on 02/11/2026 ===")
    print("Summary:")
    print("  total_total:", data_z['summary']['total_total'])
    print("  total_paid:", data_z['summary']['total_paid'])
    print("  prior_payments_total:", data_z.get('prior_payments_total'))
    print("  cheques_global_amount:", data_z.get('cheques_global_amount'))
    print("\\nCheques in data_z['cheques']:")
    for chk in data_z['cheques']:
        print(" ", chk)
    print("\\nPrior payments in data_z['prior_payments']:")
    for pp in data_z['prior_payments']:
        print(" ", pp)
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/test_report_data_0211.py', 'w') as f:
    f.write(test_script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c '/opt/odoo/odoo-venv/bin/python3 /tmp/test_report_data_0211.py'")
print(stdout.read().decode('utf-8'))
err = stderr.read().decode('utf-8')
if err:
    print('ERR:\n', err)
ssh.close()

