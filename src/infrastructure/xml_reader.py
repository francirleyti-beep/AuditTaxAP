import xml.etree.ElementTree as ET
from decimal import Decimal
from src.domain.dtos import FiscalItemDTO

class XMLReader:
    """
    Responsável por ler o arquivo XML da NFe e extrair os itens fiscais.
    Implementa a Input Layer do SPEC.
    """
    
    def parse(self, xml_path: str) -> tuple[str, list[FiscalItemDTO]]:
        """
        Lê um arquivo XML e retorna a Chave da NFe e uma lista de FiscalItemDTOs.
        Retorno: (nfe_key_limpa, lista_itens)
        """
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        # O namespace padrão da NFe é geralmente http://www.portalfiscal.inf.br/nfe
        ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
        if not root.tag.startswith('{http://www.portalfiscal.inf.br/nfe}'):
            ns = {}

        # Extrair Chave da NFe
        # A chave fica no atributo Id da tag infNFe (ex: NFe3520...)
        inf_nfe = root.find(".//nfe:infNFe", ns) if ns else root.find(".//infNFe")
        nfe_key = ""
        if inf_nfe is not None:
            raw_id = inf_nfe.get("Id", "")
            if raw_id.startswith("NFe"):
                nfe_key = raw_id[3:] # Remove prefixo 'NFe'
            else:
                nfe_key = raw_id
        
        fiscal_items = []
        # XPath: .//nfe:infNFe/nfe:det
        
        # Função auxiliar para find texto com namespace
        def get_text(node, tag, default=""):
            found = node.find(f"nfe:{tag}", ns) if ns else node.find(tag)
            return found.text if found is not None else default

        dets = root.findall(".//nfe:det", ns) if ns else root.findall(".//det")
        
        for det in dets:
            n_item_str = det.get("nItem")
            n_item = int(n_item_str) if n_item_str and n_item_str.isdigit() else 0
            
            # Produto
            prod = det.find("nfe:prod", ns) if ns else det.find("prod")
            if prod is None:
                continue # Pula se não tiver produto

            prod_vals = {
                "cProd": get_text(prod, "cProd"),
                "xProd": get_text(prod, "xProd"),
                "NCM": get_text(prod, "NCM"),
                "CEST": get_text(prod, "CEST"),
                "CFOP": get_text(prod, "CFOP"),
                "vProd": Decimal(get_text(prod, "vProd", "0.00")),
            }
            
            # Imposto (ICMS)
            imposto = det.find("nfe:imposto", ns) if ns else det.find("imposto")
            icms_node = None
            if imposto is not None:
                icms_node = imposto.find("nfe:ICMS", ns) if ns else imposto.find("ICMS")
            
            # Valores padrão
            cst = ""
            v_bc = Decimal("0.00")
            p_icms = Decimal("0.00")
            v_icms = Decimal("0.00")
            p_mvast = Decimal("0.00")
            v_icms_deson = Decimal("0.00")
            mot_des_icms = ""
            
            # Encontrar qual tag de tributação foi usada (Ex: ICMS00, ICMS40, etc)
            if icms_node is not None:
                # Pega o primeiro filho (ex: ICMS00)
                tax_group = icms_node[0] if len(icms_node) > 0 else None
                
                if tax_group is not None:
                    # Tenta ler CST ou CSOSN
                    cst = get_text(tax_group, "CST") or get_text(tax_group, "CSOSN")
                    
                    v_bc = Decimal(get_text(tax_group, "vBC", "0.00"))
                    p_icms = Decimal(get_text(tax_group, "pICMS", "0.00"))
                    v_icms = Decimal(get_text(tax_group, "vICMS", "0.00"))
                    p_mvast = Decimal(get_text(tax_group, "pMVAST", "0.00"))
                    
                    v_icms_deson = Decimal(get_text(tax_group, "vICMSDeson", "0.00"))
                    mot_des_icms = get_text(tax_group, "motDesICMS")

            # Verifica benefício Suframa (motDesICMS = 7)
            is_suframa = (mot_des_icms == "7")

            item_dto = FiscalItemDTO(
                origin="XML",
                item_index=n_item,
                product_code=prod_vals["cProd"],
                ncm=prod_vals["NCM"],
                cest=prod_vals["CEST"],
                cfop=prod_vals["CFOP"],
                cst=cst,
                amount_total=prod_vals["vProd"],
                tax_base=v_bc,
                tax_rate=p_icms,
                tax_value=v_icms,
                mva_percent=p_mvast,
                is_suframa_benefit=is_suframa
            )
            
            fiscal_items.append(item_dto)
            
        return nfe_key, fiscal_items
