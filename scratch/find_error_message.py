import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pwd = 'lOnohi_1989' + '$tm'
ssh.connect('167.172.158.168', username='root', password=pwd, timeout=20)

cmd = """python3 -c "
import os

keywords = ['compte en suspens', 'pièce comptable', 'outstanding account']
for root, dirs, files in os.walk('/opt/odoo/odoo'):
    for f in files:
        if f.endswith('.py'):
            p = os.path.join(root, f)
            try:
                with open(p, 'r', encoding='utf-8') as fp:
                    content = fp.read()
                    if 'outstanding' in content.lower() and 'cannot be confirmed' in content.lower():
                        print('Found in:', p)
                        for line in content.splitlines():
                            if 'cannot be confirmed' in line.lower() or 'outstanding' in line.lower() and 'move' in line.lower():
                                print('  ', line.strip())
            except Exception:
                pass
" """

stdin, stdout, stderr = ssh.exec_command(cmd)
print("STDOUT:\n", stdout.read().decode('utf-8'))
print("STDERR:\n", stderr.read().decode('utf-8'))
ssh.close()

