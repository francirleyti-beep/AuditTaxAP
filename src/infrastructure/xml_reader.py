from datetime import datetime
import xml.etree.ElementTree as ET
from decimal import Decimal
from src.domain.dtos import FiscalItemDTO, InvoiceDTO

class XMLReader:
    """
    Responsável por ler o arquivo XML da NFe e extrair os itens fiscais.
    Implementa a Input Layer do SPEC.
    """
    
    def parse(self, xml_path: str) -> InvoiceDTO:
        """
        Lê um arquivo XML e retorna um InvoiceDTO (Cabeçalho + Itens).
        """
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        # O namespace padrão da NFe é geralmente http://www.portalfiscal.inf.br/nfe
        ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
        if not root.tag.startswith('{http://www.portalfiscal.inf.br/nfe}'):
            ns = {}

        # Helpers
        def find(node, tag):
            if node is None:
                return None
            return node.find(f"nfe:{tag}", ns) if ns else node.find(tag)
            
        def get_text(node, tag, default=""):
            if node is None: return default
            found = find(node, tag)
            return found.text if found is not None else default

        # --- Identificação ---
        # Tenta pegar infNFe. Se nao achar direto (ex: raiz nfeProc), tenta buscar recursively
        inf_nfe = find(root, "infNFe")
        if inf_nfe is None:
             # Tenta localizar NFe/infNFe (estrutura nfeProc)
             nfe_node = find(root, "NFe")
             inf_nfe = find(nfe_node, "infNFe")
        
        # Se ainda falhar, tenta busca profunda (pode ser lento, mas seguro)
        if inf_nfe is None:
             inf_nfe = root.find(".//nfe:infNFe", ns) if ns else root.find(".//infNFe")
        
        # Chave de Acesso
        raw_id = inf_nfe.get("Id", "") if inf_nfe is not None else ""
        access_key = raw_id[3:] if raw_id.startswith("NFe") else raw_id
        
        ide = find(inf_nfe, "ide")
        n_nf = int(get_text(ide, "nNF", "0"))
        serie = int(get_text(ide, "serie", "0"))
        dh_emi_str = get_text(ide, "dhEmi")
        try:
            # Formato ISO: 2023-10-25T14:30:00-03:00
            issue_date = datetime.fromisoformat(dh_emi_str)
        except ValueError:
            issue_date = datetime.min

        # --- Emitente ---
        emit = find(inf_nfe, "emit")
        ender_emit = find(emit, "enderEmit")
        emitter_name = get_text(emit, "xNome")
        emitter_cnpj = get_text(emit, "CNPJ")
        emitter_city = get_text(ender_emit, "xMun")

        # --- Destinatário ---
        dest = find(inf_nfe, "dest")
        recipient_name = get_text(dest, "xNome")
        recipient_doc = get_text(dest, "CNPJ") or get_text(dest, "CPF")

        # --- Totais ---
        total = find(inf_nfe, "total")
        icms_tot = find(total, "ICMSTot")
        
        v_prod_total = Decimal(get_text(icms_tot, "vProd", "0.00"))
        v_nf_total = Decimal(get_text(icms_tot, "vNF", "0.00"))
        v_icms_total = Decimal(get_text(icms_tot, "vICMS", "0.00"))

        # --- Transporte ---
        transp = find(inf_nfe, "transp")
        mod_frete = get_text(transp, "modFrete")

        # --- Protocolo ---
        # Fica fora de infNFe, geralmente em nfeProc/protNFe
        # Mas estrutura varia. Tentar achar protNFe na raiz.
        prot_nfe = find(root, "protNFe")
        inf_prot = find(prot_nfe, "infProt") if prot_nfe else None
        
        prot_number = get_text(inf_prot, "nProt")
        dh_recbto_str = get_text(inf_prot, "dhRecbto")
        try:
            prot_date = datetime.fromisoformat(dh_recbto_str)
        except (ValueError, TypeError):
            prot_date = datetime.min

        # --- Itens ---
        fiscal_items = []
        dets = root.findall(".//nfe:det", ns) if ns else root.findall(".//det")
        
        for det in dets:
            n_item_str = det.get("nItem")
            n_item = int(n_item_str) if n_item_str and n_item_str.isdigit() else 0
            
            prod = find(det, "prod")
            if prod is None: continue

            # Extração de valores do item
            q_com = Decimal(get_text(prod, "qCom", "0.00"))
            v_un_com = Decimal(get_text(prod, "vUnCom", "0.00"))
            v_prod = Decimal(get_text(prod, "vProd", "0.00"))
            
            prod_vals = {
                "cProd": get_text(prod, "cProd"),
                "xProd": get_text(prod, "xProd"),
                "NCM": get_text(prod, "NCM"),
                "CEST": get_text(prod, "CEST"),
                "CFOP": get_text(prod, "CFOP"),
            }
            
            # Impostos
            imposto = find(det, "imposto")
            icms_node = None
            if imposto is not None:
                icms_node = find(imposto, "ICMS")
            
            cst = ""
            v_bc = Decimal("0.00")
            p_icms = Decimal("0.00")
            v_icms = Decimal("0.00")
            p_mvast = Decimal("0.00")
            v_icms_deson = Decimal("0.00")
            mot_des_icms = ""
            
            if icms_node is not None:
                # O XML tem apenas UM filho dentro de ICMS (ICMS00, ICMS40, etc)
                # Iterar para achar o primeiro filho
                for child in icms_node:
                    tax_group = child
                    break
                else:
                    tax_group = None

                if tax_group is not None:
                    cst = get_text(tax_group, "CST") or get_text(tax_group, "CSOSN")
                    v_bc = Decimal(get_text(tax_group, "vBC", "0.00"))
                    p_icms = Decimal(get_text(tax_group, "pICMS", "0.00"))
                    v_icms = Decimal(get_text(tax_group, "vICMS", "0.00"))
                    p_mvast = Decimal(get_text(tax_group, "pMVAST", "0.00"))
                    v_icms_deson = Decimal(get_text(tax_group, "vICMSDeson", "0.00"))
                    mot_des_icms = get_text(tax_group, "motDesICMS")

            is_suframa = (mot_des_icms == "7")

            item_dto = FiscalItemDTO(
                origin="XML",
                item_index=n_item,
                product_code=prod_vals["cProd"],
                product_description=prod_vals["xProd"], # [NEW]
                ncm=prod_vals["NCM"],
                cest=prod_vals["CEST"],
                cfop=prod_vals["CFOP"],
                cst=cst,
                quantity=q_com,        # [NEW]
                unit_price=v_un_com,   # [NEW]
                amount_total=v_prod,
                tax_base=v_bc,
                tax_rate=p_icms,
                tax_value=v_icms,
                mva_percent=p_mvast,
                is_suframa_benefit=is_suframa,
                sefaz_benefit_value=v_icms_deson
            )
            fiscal_items.append(item_dto)

        # Montar InvoiceDTO
        return InvoiceDTO(
            access_key=access_key,
            number=n_nf,
            series=serie,
            issue_date=issue_date,
            emitter_name=emitter_name,
            emitter_cnpj=emitter_cnpj,
            emitter_city=emitter_city,
            recipient_name=recipient_name,
            recipient_doc=recipient_doc,
            total_products=v_prod_total,
            total_invoice=v_nf_total,
            total_icms=v_icms_total,
            freight_mode=mod_frete,
            protocol_number=prot_number,
            protocol_date=prot_date,
            items=fiscal_items
        )
