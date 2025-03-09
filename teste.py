import re

def extrair_e_corrigir_xml(arquivo_entrada, arquivo_saida):
    # Regex para capturar as seções válidas de <InfNfse>
    padrao = r"<InfNfse[\s\S]*?</InfNfse>"

    with open(arquivo_entrada, "r", encoding="utf-8") as entrada:
        conteudo = entrada.read()

    # Encontrar todas as seções que correspondem ao padrão
    registros = re.findall(padrao, conteudo)

    # Reconstituir um XML válido
    with open(arquivo_saida, "w", encoding="utf-8") as saida:
        saida.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        saida.write('<Nfse versao="2.03">\n')
        for registro in registros:
            saida.write(f"  {registro}\n")
        saida.write('</Nfse>')

    print(f"Arquivo corrigido salvo em: {arquivo_saida}")

# Use os nomes corretos para os arquivos
arquivo_entrada = "./modelo.xml"  # Substitua pelo caminho real
arquivo_saida = "./nota_corrigida.xml"
extrair_e_corrigir_xml(arquivo_entrada, arquivo_saida)
