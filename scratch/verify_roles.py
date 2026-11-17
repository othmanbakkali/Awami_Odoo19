import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pwd = 'lOnohi_1989' + '$tm'
ssh.connect('167.172.158.168', username='root', password=pwd, timeout=20)

cmd = """su - odoo -s /bin/bash -c "/opt/odoo/odoo-venv/bin/python3 /opt/odoo/odoo/odoo-bin shell -c /etc/odoo.conf -d Hanouty --no-http << 'EOF'
mod = env['ir.module.module'].search([('name', '=', 'awami_roles_permissions')])
print('MODULE STATE:', mod.state if mod else 'NOT FOUND')

Role = env['res.users.role']
roles = Role.search([])
print('TOTAL ROLES:', len(roles))
for r in roles:
    print(f'Rôle {r.id}: {r.name} (Code: {r.code}) | Users: {len(r.user_ids)} | Modèles CRUD: {len(r.line_ids)} | Guards: inv={r.prevent_invoice_unlink}, pay={r.prevent_payment_unlink}, so={r.prevent_sale_order_unlink}')
    for line in r.line_ids[:3]:
        print(f'   - {line.name} ({line.model_name}): R={line.perm_read}, C={line.perm_create}, W={line.perm_write}, U={line.perm_unlink}')

# Check user effective rights
user = env['res.users'].search([('share', '=', False)], limit=1)
print(f'Testing User: {user.name} ({user.login})')
print('User roles:', user.roles_display)
print('User effective HTML preview (length):', len(user.effective_rights_html or ''))

# Check menus
menu_root = env.ref('awami_roles_permissions.menu_roles_permissions_root', raise_if_not_found=False)
print('Menu Root exists?:', bool(menu_root))
menu_roles = env.ref('awami_roles_permissions.menu_res_users_role_main', raise_if_not_found=False)
print('Menu Roles exists?:', bool(menu_roles))
EOF
" """

stdin, stdout, stderr = ssh.exec_command(cmd)
print("STDOUT:\n", stdout.read().decode('utf-8'))
print("STDERR:\n", stderr.read().decode('utf-8'))
ssh.close()

