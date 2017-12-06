from django.core.files.storage import Storage
from django.conf import settings

from fdfs_client.client import Fdfs_client
class FDFSStorage(Storage):

    """fdfs文件存储系统"""
    def __init__(self, client_conf = None, nginx_url = None):
        """初始化"""
        if client_conf is None:
            client_conf = settings.FDFS_CLIENT_CONF
        self.client_conf = client_conf

        if nginx_url is None:
            nginx_url = settings.FDFS_NGINX_URL
        self.nginx_url = nginx_url

    def _open(self, name, mode = 'rb' ):
        """打开文件使用"""
        pass
    def _save(self, name, content):
        """保存文件的时候使用"""
        # name ：上传文件的名称
        # content： 包含上传文件内容的File对象
        # {
        #     'Group name': group_name,
        #     'Remote file_id': remote_file_id,
        #     'Status': 'Upload successed.',
        #     'Local file name': '',
        #     'Uploaded size': upload_size,
        #     'Storage IP': storage_ip
        # }
        # 上传文件到fdfs系统中
        client = Fdfs_client(self.client_conf)
        # 获取上传文件的内容
        content = content.read()
        # 调用upload_by_buffer()
        res = client.upload_by_buffer(content)
        # 判断是否上传成功
        if res['Status'] != 'Upload successed.':
            raise Exception('上传文件到fdfs失败')


        # 获取文件的id
        file_id= res['Remote file_id']

        # 返回文件的id

        return file_id

    def exists(self, name):
        """判断文件在本地文件系统中是否存在"""
        return False

    def url(self, name):

        """返回可访问到name文件的URL路径"""

        return self.nginx_url + name








