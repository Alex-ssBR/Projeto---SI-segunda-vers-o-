import os

class Config:
    SECRET_KEY = 'sua_chave_secreta_aqui'
    # O @ no final da senha foi substituído por %40
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:Root1234%40@localhost/gestao_chamados'
    SQLALCHEMY_TRACK_MODIFICATIONS = False