import os
from flask import Flask, render_template, request, flash, redirect, url_for
from werkzeug.utils import secure_filename
import xml.etree.ElementTree as ET 
import json 

app = Flask(__name__)
app.secret_key = "xml_e_flask_sao_demais_123"

ALLOWED_EXTENSIONS = {'xml'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def parse_nfe_xml(xml_string):
    """
    Analisa uma string XML de NF-e e extrai os dados relevantes.
    Retorna um dicionário com os dados ou um dicionário de erro.
    """
    try:
        namespaces = {'ns': 'http://www.portalfiscal.inf.br/nfe'}
        
        root = ET.fromstring(xml_string)
        
        infNFe = root.find('.//ns:infNFe', namespaces)
        if infNFe is None:
            nfe_node = root.find('.//ns:NFe', namespaces)
            if nfe_node is not None:
                infNFe = nfe_node.find('.//ns:infNFe', namespaces)

        if infNFe is None:
            return {"erro": "Tag <infNFe> não encontrada no XML. Verifique a estrutura e o namespace."}

        dados_nota = {}

        # Emitente (Fornecedor)
        emit_node = infNFe.find('ns:emit', namespaces)
        if emit_node is not None:
            nome_fornecedor = emit_node.findtext('ns:xNome', None, namespaces)
            if nome_fornecedor is not None and nome_fornecedor.strip() != '':
                dados_nota['fornecedor_nome'] = nome_fornecedor.strip()
            else:
                dados_nota['fornecedor_nome'] = None
        else:
            dados_nota['fornecedor_nome'] = None

        # Data de Emissão
        ide_node = infNFe.find('ns:ide', namespaces)
        if ide_node is not None:
            dhEmi = ide_node.findtext('ns:dhEmi', None, namespaces)
            if dhEmi and dhEmi.strip() != '':
                dados_nota['data_emissao'] = dhEmi.split('T')[0]
            else:
                dados_nota['data_emissao'] = None
        else:
            dados_nota['data_emissao'] = None
            

        # Valor Total da Nota
        total_node = infNFe.find('ns:total/ns:ICMSTot', namespaces) # Caminho para ICMSTot dentro de total
        if total_node is not None:
            vNF_text = total_node.findtext('ns:vNF', None, namespaces)
            dados_nota['valor_total'] = float(vNF_text) if vNF_text else None
        else:
            dados_nota['valor_total'] = None

        # Itens da Nota
        dados_nota['itens'] = []
        for det_node in infNFe.findall('ns:det', namespaces):
            item = {}
            prod_node = det_node.find('ns:prod', namespaces)
            if prod_node is not None:
                codigo_produto = prod_node.findtext('ns:cProd', None, namespaces)
                descricao = prod_node.findtext('ns:xProd', None, namespaces)
                qCom_text = prod_node.findtext('ns:qCom', None, namespaces)
                unidade = prod_node.findtext('ns:uCom', None, namespaces)
                vUnCom_text = prod_node.findtext('ns:vUnCom', None, namespaces)
                vProd_text = prod_node.findtext('ns:vProd', None, namespaces)
                item['codigo_produto'] = codigo_produto.strip() if codigo_produto and codigo_produto.strip() != '' else None
                item['descricao'] = descricao.strip() if descricao and descricao.strip() != '' else None
                item['quantidade'] = float(qCom_text) if qCom_text and qCom_text.strip() != '' else None
                item['unidade'] = unidade.strip() if unidade and unidade.strip() != '' else None
                item['valor_unitario'] = float(vUnCom_text) if vUnCom_text and vUnCom_text.strip() != '' else None
                item['valor_total_item'] = float(vProd_text) if vProd_text and vProd_text.strip() != '' else None
                dados_nota['itens'].append(item)

        # Faturas e duplicatas (caso existam)
        cobr_node = infNFe.find('ns:cobr', namespaces)
        if cobr_node is not None:
            fat_node = cobr_node.find('ns:fat', namespaces)
            if fat_node is not None:
                nFat = fat_node.findtext('ns:nFat', None, namespaces)
                vOrig = fat_node.findtext('ns:vOrig', '0', namespaces)
                vDesc = fat_node.findtext('ns:vDesc', '0', namespaces)
                vLiq = fat_node.findtext('ns:vLiq', '0', namespaces)
                dados_nota['fatura'] = {
                    'numero': nFat.strip() if nFat and nFat.strip() != '' else None,
                    'valor_original': float(vOrig) if vOrig and vOrig.strip() != '' else 0.0,
                    'valor_desconto': float(vDesc) if vDesc and vDesc.strip() != '' else 0.0,
                    'valor_liquido': float(vLiq) if vLiq and vLiq.strip() != '' else 0.0,
                }
            else:
                dados_nota['fatura'] = None
            dados_nota['duplicatas'] = []
            for dup_node in cobr_node.findall('ns:dup', namespaces):
                nDup = dup_node.findtext('ns:nDup', None, namespaces)
                dVenc = dup_node.findtext('ns:dVenc', None, namespaces)
                vDup = dup_node.findtext('ns:vDup', '0', namespaces)
                duplicata = {
                    'numero': nDup.strip() if nDup and nDup.strip() != '' else None,
                    'vencimento': dVenc.strip() if dVenc and dVenc.strip() != '' else None,
                    'valor': float(vDup) if vDup and vDup.strip() != '' else 0.0,
                }
                dados_nota['duplicatas'].append(duplicata)
        else:
            dados_nota['fatura'] = None
            dados_nota['duplicatas'] = []
        
        return {"success": True, "data": dados_nota}

    except ET.ParseError as e:
        print(f"Erro de parsing do XML: {e}")
        return {"erro": f"XML malformado ou inválido: {e}"}
    except Exception as e:
        print(f"Erro inesperado ao processar XML: {e}")
        return {"erro": f"Erro inesperado durante o processamento do XML: {str(e)}"}


@app.route('/', methods=['GET', 'POST'])
def index():
    nome_do_arquivo_recebido = None
    dados_nota_fiscal = None 
    erro_processamento = None

    if request.method == 'POST':
        if 'nota_fiscal_file' not in request.files:
            flash('Nenhum arquivo XML selecionado!', 'error')
            return redirect(request.url)
        
        file = request.files['nota_fiscal_file']
        
        if file.filename == '':
            flash('Nenhum arquivo XML selecionado!', 'error')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            nome_do_arquivo_recebido = filename
            
            try:
                xml_string_content = file.read().decode('utf-8')
                
                resultado_parse = parse_nfe_xml(xml_string_content)
                
                if resultado_parse.get("success"):
                    dados_nota_fiscal = resultado_parse["data"]
                    flash(f'XML "{filename}" processado com sucesso!', 'success')
                else:
                    erro_processamento = resultado_parse.get("erro", "Erro desconhecido no parsing do XML.")
                    flash(f'Erro ao processar XML: {erro_processamento}', 'error')

            except Exception as e:
                erro_processamento = f'Erro ao ler ou processar o arquivo XML: {str(e)}'
                flash(erro_processamento, 'error')
                print(f"Erro na leitura/processamento do arquivo: {e}")
            
            return render_template('index.html', 
                                   nome_arquivo=nome_do_arquivo_recebido, 
                                   dados_nota=dados_nota_fiscal, # Passando os dados parseados
                                   erro_parse=erro_processamento) 
        else:
            flash('Tipo de arquivo não permitido! Apenas arquivos .xml são aceitos.', 'error')
            return redirect(request.url)
            
    return render_template('index.html', 
                           nome_arquivo=nome_do_arquivo_recebido, 
                           dados_nota=dados_nota_fiscal,
                           erro_parse=erro_processamento)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=os.environ.get('PORT', 5000))