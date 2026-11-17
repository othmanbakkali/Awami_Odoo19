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
    
    # 1. Test account.z.report for 2026-11-02
    z_rep = env['account.z.report'].create({
        'company_id': 1,
        'date_start': '2026-11-02',
        'date_end': '2026-11-02',
    })
    z_data = z_rep.get_report_data()
    print("=== account.z.report on 2026-11-02 ===")
    print("cheques_count:", len(z_data.get('cheques', [])))
    for c in z_data.get('cheques', []):
        print("  Cheque:", c)

    # 2. Test account.sales.expense.report for 2026-11-02
    se_rep = env['account.sales.expense.report'].create({
        'company_id': 1,
        'date_start': '2026-11-02',
        'date_end': '2026-11-02',
    })
    se_data = se_rep.get_report_data()
    print("\\n=== account.sales.expense.report on 2026-11-02 ===")
    print("cheques_count:", len(se_data.get('cheques', [])))
    for c in se_data.get('cheques', []):
        print("  Cheque:", c)

    # 3. Test on 2026-11-11
    z_rep11 = env['account.z.report'].create({
        'company_id': 1,
        'date_start': '2026-11-11',
        'date_end': '2026-11-11',
    })
    z_data11 = z_rep11.get_report_data()
    print("\\n=== account.z.report on 2026-11-11 ===")
    print("cheques_count:", len(z_data11.get('cheques', [])))
    for c in z_data11.get('cheques', []):
        print("  Cheque:", c)
"""

with sftp.file('/tmp/test_rep_cheques.py', 'w') as f:
    f.write(remote_script)

stdin, stdout, stderr = ssh.exec_command('su - odoo -s /bin/bash -c "PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/test_rep_cheques.py"')
print(stdout.read().decode('utf-8'))
print(stderr.read().decode('utf-8'))

