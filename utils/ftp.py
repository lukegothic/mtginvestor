import os, io
from ftplib import FTP
def upload(file, filename, ftpaddress="access782277410.webspace-data.io", ftppath="/upload"):
    # connect
    ftp = FTP()
    ftp.set_debuglevel(2)
    ftp.connect(ftpaddress, 21) 
    ftp.login("u97215176","aA12345678*")
    ftp.cwd(ftppath)
    # check if path or bytes
    if type(file) == "str":
        with open(filename, 'rb') as f:
            file = f.read()
    # store on ftp
    ftp.storbinary('STOR %s' % os.path.basename(filename), io.BytesIO(file), 1024)