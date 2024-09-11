import os

class Config(object):
    # 獲取當前文件的目錄
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

    # Flask 配置
    SECRET_KEY = 'your_secret_key_here'
    SEND_FILE_MAX_AGE_DEFAULT = 0  # 禁用靜態文件緩存

    # 數據庫配置
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:@localhost/project'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = ''
    MYSQL_DB = 'project'
    MYSQL_HOST = '127.0.0.1'

    # 文件上傳配置
    STATIC_FOLDER = os.path.join(BASE_DIR, 'static')
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    OUTPUT_FOLDER = os.path.join(BASE_DIR, 'static', 'outputs')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

    @classmethod
    def init_app(cls, app):
        # 確保目錄存在
        os.makedirs(cls.STATIC_FOLDER, exist_ok=True)
        os.makedirs(cls.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(cls.OUTPUT_FOLDER, exist_ok=True)
