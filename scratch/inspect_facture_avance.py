import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pwd = 'lOnohi_1989' + '$tm'
ssh.connect('167.172.158.168', username='root', password=pwd)

stdin, stdout, stderr = ssh.exec_command("find /opt/odoo/custom-addons/report_facture_avance -type f -exec head -n 100 {} +")
print("REPORT_FACTURE_AVANCE FILES:")
print(stdout.read().decode())

stdin, stdout, stderr = ssh.exec_command("find /opt/odoo/custom-addons/awami_suivi_cheques/security -type f -exec head -n 100 {} +")
print("AWAMI_SUIVI_CHEQUES SECURITY:")
print(stdout.read().decode())

ssh.close()

