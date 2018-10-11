cd /local
wget https://github.com/LCBRU/lbrc_upload/archive/master.zip
unzip master.zip
rm master.zip
rm -fR lbrc_upload
mv lbrc_upload-master lbrc_upload
cp /local/application.cfg /local/lbrc_upload/upload/

echo
echo Now run...
echo
echo sudo /etc/init.d/uol.apache2 graceful
echo