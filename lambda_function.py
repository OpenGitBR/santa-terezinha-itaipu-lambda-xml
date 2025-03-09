import os
import xml.etree.ElementTree as ET
import psycopg2
import logging
import boto3
from psycopg2 import sql

# Configuração de logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# Conectar ao banco de dados PostgreSQLa
def get_db_connection():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )

# Função principal do Lambda
def lambda_handler(event, context):
    s3_client = boto3.client('s3')

    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']

        # Fazer o download do arquivo XML do S3
        xml_file_path = f"/tmp/{key.split('/')[-1]}"
        logger.info(f"Baixando arquivo {key} do bucket {bucket}...")
        
        s3_client.download_file(bucket, key, xml_file_path)
        logger.info(f"Arquivo {key} baixado com sucesso.")

        # Extrair dados do XML
        notas = processar_xml(xml_file_path)

        # Inserir dados no PostgreSQL
        inserir_nfs(notas)

    return {"statusCode": 200, "body": "Processo concluído"}

# Função para processar o XML e extrair os dados necessários
def processar_xml(xml_file_path):
    logger.info(f"Processando arquivo XML: {xml_file_path}")
    tree = ET.parse(xml_file_path)
    root = tree.getroot()
    namespace = {"ns": "http://www.betha.com.br/e-nota-contribuinte-ws"}

    notas = []
    for comp_nfse in root.findall(".//ns:CompNfse", namespace):
        nfse_data = {
            "cnpj_prestador": comp_nfse.findtext(".//ns:Cnpj", namespaces=namespace),
            "razao_social_tomador": comp_nfse.findtext(".//ns:RazaoSocial", namespaces=namespace),
            "numero_nsfe": comp_nfse.findtext(".//ns:Numero", namespaces=namespace),
            "competencia": comp_nfse.findtext(".//ns:Competencia", namespaces=namespace),
            "data_emissao_nfse": comp_nfse.findtext(".//ns:DataEmissao", namespaces=namespace),
            "cancelada": comp_nfse.findtext(".//ns:Sucesso", namespaces=namespace) == "false",
            "iss_retido": comp_nfse.findtext(".//ns:IssRetido", namespaces=namespace),
            "valor_servicos": comp_nfse.findtext(".//ns:ValorServicos", namespaces=namespace),
            "desconto_incondicionado": comp_nfse.findtext(".//ns:DescontoIncondicionado", namespaces=namespace),
            "base_calculo": comp_nfse.findtext(".//ns:BaseCalculo", namespaces=namespace),
            "valor_liquido_nfse": comp_nfse.findtext(".//ns:ValorLiquidoNfse", namespaces=namespace),
            "aliquota_servicos": comp_nfse.findtext(".//ns:Aliquota", namespaces=namespace),
            "valor_iss": comp_nfse.findtext(".//ns:ValorIss", namespaces=namespace),
            "municipio_prestacao_servico": comp_nfse.findtext(".//ns:CodigoMunicipio", namespaces=namespace),
            "item_lista_servico": comp_nfse.findtext(".//ns:ItemListaServico", namespaces=namespace)
        }
        notas.append(nfse_data)

    logger.info(f"{len(notas)} notas extraídas do arquivo XML.")
    return notas

# Função para inserir dados no PostgreSQL
def inserir_nfs(notas):
    connection = get_db_connection()
    cursor = connection.cursor()
    insert_query = sql.SQL("""
        INSERT INTO nfs (
            cnpj_prestador, razao_social_tomador, numero_nsfe, competencia, 
            data_emissao_nfse, cancelada, iss_retido, valor_servicos, 
            desconto_incondicionado, base_calculo, valor_liquido_nfse, 
            aliquota_servicos, valor_iss, municipio_prestacao_servico, 
            item_lista_servico
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """)

    for nota in notas:
        try:
            cursor.execute(insert_query, (
                nota["cnpj_prestador"],
                nota["razao_social_tomador"],
                nota["numero_nsfe"],
                nota["competencia"],
                nota["data_emissao_nfse"],
                nota["cancelada"],
                nota["iss_retido"],
                nota["valor_servicos"],
                nota["desconto_incondicionado"],
                nota["base_calculo"],
                nota["valor_liquido_nfse"],
                nota["aliquota_servicos"],
                nota["valor_iss"],
                nota["municipio_prestacao_servico"],
                nota["item_lista_servico"]
            ))
            logger.info(f"Nota {nota['numero_nsfe']} inserida com sucesso.")
        except Exception as e:
            logger.error(f"Erro ao inserir a nota {nota['numero_nsfe']}: {str(e)}")
    
    connection.commit()
    cursor.close()
    connection.close()
    logger.info("Todas as notas foram processadas e inseridas no banco de dados.")
