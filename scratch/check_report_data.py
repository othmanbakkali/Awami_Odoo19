import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pwd = 'lOnohi_1989' + '$tm'
ssh.connect('167.172.158.168', username='root', password=pwd, timeout=20)

remote_script = r'''
import odoo
from odoo.modules.registry import Registry
from odoo import api, SUPERUSER_ID

odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
registry = Registry('Hanouty')
with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    print("=== CHECKING Etat_Vente_Journalier_facture ===")
    z_reports = env['account.z.report'].search([], order='id desc', limit=3)
    for z in z_reports:
        print("Z Report id=" + str(z.id) + " name=" + str(z.name) + " company=" + str(z.company_id.name))
        try:
            data = z.get_report_data()
            for inv in data.get('invoices', []):
                if inv.get('name') in ['BL/2026/11/02/0020', 'BL/2026/11/02/0021', 'BL/2026/11/02/0028']:
                    print("  " + str(inv.get('name')) + " partner=" + str(inv.get('partner')) + " mode=" + str(inv.get('payment_mode')) + " check_client=" + str(inv.get('check_client_name')) + " check_num=" + str(inv.get('check_number')))
        except Exception as e:
            print("  Error:", e)

    print("=== CHECKING Report (account.sales.expense.report) ===")
    se_reports = env['account.sales.expense.report'].search([], order='id desc', limit=3)
    for se in se_reports:
        print("SE Report id=" + str(se.id) + " name=" + str(se.name) + " company=" + str(se.company_id.name))
        try:
            data = se.get_report_data()
            for inv in data.get('invoices', []):
                if inv.get('name') in ['BL/2026/11/02/0020', 'BL/2026/11/02/0021', 'BL/2026/11/02/0028']:
                    print("  " + str(inv.get('name')) + " partner=" + str(inv.get('partner')) + " mode=" + str(inv.get('payment_mode')) + " check_client=" + str(inv.get('check_client_name')) + " check_num=" + str(inv.get('check_number')))
        except Exception as e:
            print("  Error:", e)
'''

sftp = ssh.open_sftp()
with sftp.file('/tmp/check_report_data.py', 'w') as f:
    f.write(remote_script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c 'PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/check_report_data.py'")
print("STDOUT:\n", stdout.read().decode('utf-8'))
print("STDERR:\n", stderr.read().decode('utf-8'))
ssh.close()
