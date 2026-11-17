import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pwd = 'lOnohi_1989' + '$tm'
ssh.connect('167.172.158.168', username='root', password=pwd, timeout=20)

cmd = """su - odoo -s /bin/bash -c "/opt/odoo/odoo-venv/bin/python3 /opt/odoo/odoo/odoo-bin shell -c /etc/odoo.conf -d Hanouty --no-http << 'EOF'
xml_ids = [
    'sales_team.group_sale_salesman',
    'sales_team.group_sale_salesman_all_leads',
    'sales_team.group_sale_manager',
    'account.group_account_invoice',
    'account.group_account_readonly',
    'account.group_account_user',
    'account.group_account_manager',
    'stock.group_stock_user',
    'stock.group_stock_manager',
    'purchase.group_purchase_user',
    'purchase.group_purchase_manager',
    'base.group_system',
]
for x in xml_ids:
    g = env.ref(x, raise_if_not_found=False)
    print(x, ':', g.id if g else 'NOT FOUND', '| name:', g.name if g else '')
EOF
" """

stdin, stdout, stderr = ssh.exec_command(cmd)
print("STDOUT:\n", stdout.read().decode('utf-8'))
print("STDERR:\n", stderr.read().decode('utf-8'))
ssh.close()

