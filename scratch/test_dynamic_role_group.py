import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pwd = 'lOnohi_1989' + '$tm'
ssh.connect('167.172.158.168', username='root', password=pwd, timeout=20)

cmd = """su - odoo -s /bin/bash -c "/opt/odoo/odoo-venv/bin/python3 /opt/odoo/odoo/odoo-bin shell -c /etc/odoo.conf -d Hanouty --no-http << 'EOF'
# Test creating a group and ir.model.access dynamically
sale_model = env['ir.model'].search([('model', '=', 'sale.order')], limit=1)
print('Sale model found:', sale_model.id, sale_model.name)

test_grp = env['res.groups'].create({'name': 'Test Role Group'})
print('Test group created:', test_grp.id)

access = env['ir.model.access'].create({
    'name': 'test.access',
    'model_id': sale_model.id,
    'group_id': test_grp.id,
    'perm_read': True,
    'perm_write': True,
    'perm_create': True,
    'perm_unlink': False,
})
print('Access created:', access.id)

# Clean up
access.unlink()
test_grp.unlink()
print('Cleaned up successfully!')
EOF
" """

stdin, stdout, stderr = ssh.exec_command(cmd)
print("STDOUT:\n", stdout.read().decode('utf-8'))
print("STDERR:\n", stderr.read().decode('utf-8'))
ssh.close()

