from testsite.models import *

class RateCalc:
    
    def __init__(self, order, pcc_name, amount, amount_type):
        self.order = order
        self.pcc_name = pcc_name
        self.amount = amount
        self.amount_type = amount_type

    def calculate_rate(self):
        # print(self.order)
        #### Разбор пары
        currency_to_sell = ExchangeID.objects.filter(Name_RUS=self.order['ExchangeType']).values_list('SendCurrencyISO', flat=True)[0]
        currency_to_buy = ExchangeID.objects.filter(Name_RUS=self.order['ExchangeType']).values_list('ReceiveCurrencyISO', flat=True)[0]

        opertype = ExchangeID.objects.filter(Name_RUS=self.order['ExchangeType']).values_list('OperTypes', flat=True)[0]
        # print(opertype)
        OPRTs = []
        if ';' in opertype:
            while ';' in opertype:
                oprt = opertype[:opertype.find(";")].strip()
                OPRTs.append(oprt)
                opertype = opertype[opertype.find(";") + 1:].strip()
            OPRTs.append(opertype.strip())
        else:
            OPRTs.append(opertype.strip())
        # print(OPRTs)
        if len(OPRTs) == 1:
            currency_value = float(Currency_source.objects.filter(OperType=OPRTs[0],
                                                                  FinOfficeFrom=self.order['FinOfficeFrom'],
                                                                  FinOfficeTo=self.order['FinOfficeTo'],
                                                                  QuotesRC=PCCNTR_OperTypes.objects.filter(
                                                                      PCCNTR=self.pcc_name.PCCNTR_code,
                                                                      OperType=OPRTs[0]).values_list('QuotesRC',
                                                                                                     flat=True)[
                                                                      0]).values_list('Value', flat=True)[0])
            commission_record = CURR_COGS_COMMISSION.objects.filter(PCCNTR=self.pcc_name.PCCNTR_code,
                                                                    ReceiveCurrencyISO=self.order['ReceiveCurrencyISO'],
                                                                    receiveTRNSFRTYPE=self.order['ReceiveTransferType']
                                                                    ).first()
            if commission_record:
                value_commission_abs = commission_record.VALUE_COMMISSION_ABS
                value_commission = commission_record.VALUE_COMMISSION
                value_cogs = commission_record.VALUE_COGS
            else:
                value_commission_abs, value_commission, value_cogs = 0, 0, 0
            if self.amount_type == 'receive':
                currency_full_value = round(float(self.amount) * currency_value * (1 + value_commission + value_cogs), 2) - value_commission_abs
                exchange_rate = currency_full_value / self.amount
            elif self.amount_type == 'send':
                currency_full_value = round(float(self.amount + value_commission_abs) / currency_value / (1 + value_commission + value_cogs), 2)
                exchange_rate = currency_full_value * self.amount
            # print(float(self.order['SendAmount']))
            # print(currency_value)
            # print(ReceiveAmount)

        elif len(OPRTs) == 2:
            currency_value_1 = float(Currency_source.objects.filter(OperType=OPRTs[0],
                                                                    FinOfficeFrom=self.order['FinOfficeFrom'],
                                                                    FinOfficeTo='TRC20',
                                                                    QuotesRC=PCCNTR_OperTypes.objects.filter(
                                                                        PCCNTR=self.pcc_name.PCCNTR_code,
                                                                        OperType=OPRTs[0]).values_list(
                                                                        'QuotesRC', flat=True)[
                                                                        0]).values_list('Value', flat=True)[
                                         0])
            currency_value_2 = float(Currency_source.objects.filter(OperType=OPRTs[1],
                                                                    FinOfficeFrom='TRC20',
                                                                    FinOfficeTo=self.order['FinOfficeTo'],
                                                                    QuotesRC=
                                                                    PCCNTR_OperTypes.objects.filter(
                                                                        PCCNTR=self.pcc_name.PCCNTR_code,
                                                                        OperType=OPRTs[0]).values_list(
                                                                        'QuotesRC', flat=True)[
                                                                        0]).values_list('Value', flat=True)[
                                         0])
            commission_record_1 = CURR_COGS_COMMISSION.objects.filter(PCCNTR=self.pcc_name.PCCNTR_code,
                                                                    ReceiveCurrencyISO=self.order['ReceiveCurrencyISO'],
                                                                    receiveTRNSFRTYPE=self.order['ReceiveTransferType']
                                                                    ).first()
            if commission_record_1:
                value_commission_abs_1 = commission_record_1.VALUE_COMMISSION_ABS
                value_commission_1 = commission_record_1.VALUE_COMMISSION
                value_cogs_1 = commission_record_1.VALUE_COGS
            else:
                value_commission_abs_1, value_commission_1, value_cogs_1 = 0, 0, 0
            
            commission_record_2 = CURR_COGS_COMMISSION.objects.filter(PCCNTR=self.pcc_name.PCCNTR_code,
                                                                    ReceiveCurrencyISO=self.order['ReceiveCurrencyISO'],
                                                                    receiveTRNSFRTYPE=self.order['ReceiveTransferType']
                                                                    ).first()
            if commission_record_1:
                value_commission_abs_2 = commission_record_2.VALUE_COMMISSION_ABS
                value_commission_2 = commission_record_2.VALUE_COMMISSION
                value_cogs_2 = commission_record_2.VALUE_COGS
            else:
                value_commission_abs_2, value_commission_2, value_cogs_2 = 0, 0, 0
            if self.amount_type == 'receive':
                currency_full_value_1 = round(float(self.amount) * currency_value_1 * (1 + value_commission_1 + value_cogs_1), 2) - value_commission_abs_1
                currency_full_value = round(float(currency_full_value_1) * currency_value_2 * (1 + value_commission_2 + value_cogs_2), 2) - value_commission_abs_2
                exchange_rate = currency_full_value / self.amount
            elif self.amount_type == 'send':
                currency_full_value_1 = round(float(self.amount + value_commission_abs_1) / currency_value_1 / (1 + value_commission_1 + value_cogs_1), 2)
                currency_full_value = round(float(currency_full_value_1) * currency_value_2 * (1 + value_commission_2 + value_cogs_2), 2) + value_commission_abs_2
                exchange_rate = currency_full_value / self.amount
        return currency_full_value, exchange_rate
        