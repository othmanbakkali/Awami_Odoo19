import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pwd = 'lOnohi_1989' + '$tm'
ssh.connect('167.172.158.168', username='root', password=pwd, timeout=20)

cmd = """su - odoo -s /bin/bash -c "/opt/odoo/odoo-venv/bin/python3 /opt/odoo/odoo/odoo-bin shell -c /etc/odoo.conf -d Hanouty --no-http << 'EOF'
tree_view = env.ref('account.view_account_payment_tree', raise_if_not_found=False)
print('account.view_account_payment_tree exists?:', bool(tree_view))
if not tree_view:
    views = env['ir.ui.view'].search([('model', '=', 'account.payment'), ('type', '=', 'list')])
    for v in views:
        print('LIST VIEW:', v.id, v.xml_id, v.name)
reg_view = env.ref('account.view_account_payment_register_form', raise_if_not_found=False)
print('account.view_account_payment_register_form exists?:', bool(reg_view))
form_view = env.ref('account.view_account_payment_form', raise_if_not_found=False)
print('account.view_account_payment_form exists?:', bool(form_view))
EOF
" """

stdin, stdout, stderr = ssh.exec_command(cmd)
print("STDOUT:", stdout.read().decode('utf-8'))
print("STDERR:", stderr.read().decode('utf-8'))
ssh.close()

