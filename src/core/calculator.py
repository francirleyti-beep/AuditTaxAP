from decimal import Decimal, ROUND_HALF_UP

class TaxCalculator:
    """
    Responsável por realizar os cálculos tributários (ICMS-ST, MVA Ajustada, Suframa).
    """

    def __init__(self):
        # Contexto padrão para arredondamento monetário
        self.context = Decimal("0.01")

    def round_decimal(self, value: Decimal) -> Decimal:
        return value.quantize(self.context, rounding=ROUND_HALF_UP)

    def calculate_adjusted_mva(self, mva_original: Decimal, alq_inter: Decimal, alq_intra: Decimal) -> Decimal:
        """
        Calcula a MVA Ajustada.
        Fórmula: MVA Ajustada = [(1 + MVA-ST original) * (1 - ALQ inter) / (1 - ALQ intra)] - 1
        """
        # Exemplo de fórmula visual:
        # (1 + 0.40) * (1 - 0.12) / (1 - 0.18) - 1
        
        factor_mva = (Decimal("1") + (mva_original / 100))
        factor_inter = (Decimal("1") - (alq_inter / 100))
        factor_intra = (Decimal("1") - (alq_intra / 100))

        if factor_intra == 0:
            raise ValueError("Alíquota Intra não pode ser 100% (divisão por zero).")

        mva_adjusted = (factor_mva * factor_inter / factor_intra) - Decimal("1")
        return self.round_decimal(mva_adjusted * 100)

    def calculate_icms_st(self, base_calc: Decimal, mva: Decimal, alq_intra: Decimal, valor_icms_proprio: Decimal) -> Decimal:
        """
        Calcula o valor do ICMS ST.
        Base ST = Base Calc * (1 + MVA/100)
        ICMS ST = (Base ST * Alq Intra/100) - ICMS Próprio
        """
        base_st = base_calc * (Decimal("1") + (mva / 100))
        base_st = self.round_decimal(base_st)
        
        debit_st = base_st * (alq_intra / 100)
        debit_st = self.round_decimal(debit_st)
        
        icms_st = debit_st - valor_icms_proprio
        
        # O valor do imposto não pode ser negativo
        return max(Decimal("0.00"), self.round_decimal(icms_st))
