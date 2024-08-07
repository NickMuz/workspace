import pandas as pd 
import yfinance as yf
from datetime import datetime
import math
from tqdm import tqdm
import numpy as np
import matplotlib.pyplot as plt  
from pprint import pprint


# https://github.com/ranaroussi/yfinance
# https://pypi.org/project/yfinance/

class ACAO():
        
    def __init__(self,quantidade_de_acao_prospectada,ativos,CARTEIRA,valor_disponivel) -> None:
        self.ativos=ativos
        self.quantidade_de_acao_prospectada = quantidade_de_acao_prospectada
        self.carteira=CARTEIRA
        self.valor_disponivel = valor_disponivel

    def start(self):
        pd.reset_option('max_columns')
        df =pd.DataFrame([],columns=['VALOR_PROSPECTADO_DIV_MEDIO','VALOR_REAL_DIV_MEDIO','ACAO','PRECO','VALOR_COMPRA','PRECOJUSTO','PRECOTETO_8','PRECOTETO_10','DIV.MEDIO','V/VP','EV/EBITDA','VARIACAO'])
        for x,y in enumerate(self.ativos):
            self.get_dados(x,y,df)
        df = df.sort_values(['VALOR_PROSPECTADO_DIV_MEDIO'], ascending=[False])
        print('######################### POSSIVEL OPORTUNIDADE DE COMPRAR ##################################')
        dd = df[ (df['PRECO']-df['VALOR_COMPRA']<=0) & (df['PRECO']-df['PRECOJUSTO']<=0)& (df['PRECO']-df['PRECOTETO_8']<=0) & (df['EV/EBITDA']<=10.0) & (df['EV/EBITDA']>0.0)]

        dd = dd[['ACAO','PRECO','VALOR_COMPRA','PRECOJUSTO','PRECOTETO_8','PRECOTETO_10','V/VP','EV/EBITDA','VARIACAO']]
        dd['VALOR_DISPONIVEL'] = dd['PRECO'].apply(lambda x : x*  (self.valor_disponivel/ (dd['PRECO'].sum())))
        dd['QUANTIDADE_ACAO']  = round(dd['VALOR_DISPONIVEL']/dd['PRECO'],2)

        pprint(dd)

        print('######################### POSSIVEL OPORTUNIDADE DE VENDER  ##################################')
        dd0 =  df[(df['PRECO']-df['VALOR_COMPRA']>0) & (df['EV/EBITDA']>=10.0) ]
        dd0 =  dd0[ (dd0['VARIACAO']>0)]
        dd0 =  dd0[['ACAO','PRECO','VALOR_COMPRA','PRECOJUSTO','PRECOTETO_8','PRECOTETO_10','V/VP','EV/EBITDA','VARIACAO']]
        print(dd0)
        print('####################################################################')
        print(df)
        print('####################################################################')
        # self.GRAFICO(dd,"COMPRAR")
        # self.GRAFICO(dd0,"VENDER")

        # dd1 = df[['ACAO','VALOR_PROSPECTADO_DIV_MEDIO','VALOR_REAL_DIV_MEDIO']]
        # print("VALOR A APLICAR:",self.quantidade_de_acao_prospectada)
        # print('DIVIDENDO TOTAL ANO:',df['VALOR_REAL_DIV_MEDIO'].sum())
        # print(dd1)


    def get_dados(self,index,acao,df):
        aapl = yf.Ticker(f"{acao}.SA")
        VPA=aapl.info['bookValue']
        PL = aapl.info['trailingPE']
        LPA =aapl.info['trailingEps']
        num= (2.25* PL* VPA*LPA)
        preco_justo = math.pow(num, 1/2)
        dividendo_medio_5= pd.Series(aapl.dividends.resample('YE').sum()).tail(3).mean()         #3 anos
        preco_teto = round(dividendo_medio_5/0.06,2)
        df.loc[index,'ACAO']=acao
        df.loc[index,'PRECO']=aapl.info['currentPrice']
        df.loc[index,'VARIACAO']= round(aapl.info['52WeekChange']*100,2) if "52WeekChange" in aapl.info else 0.0
        df.loc[index,'PRECOJUSTO']= round(preco_justo,2)
        df.loc[index,'VALOR_COMPRA']= round(preco_justo*0.95,2)
        df.loc[index,'DIV.MEDIO']=round(float(dividendo_medio_5),2)
        df.loc[index,'VALOR_PROSPECTADO_DIV_MEDIO'] =   round((self.quantidade_de_acao_prospectada/aapl.info['currentPrice']) * dividendo_medio_5,2)
        df.loc[index,'VALOR_REAL_DIV_MEDIO']=round(self.carteira[index]*dividendo_medio_5,2)
        # df.loc[index,'PRECOTETO_8']=round(float(dividendo_medio_5)/0.08,2)
        df.loc[index,'PRECOTETO_8']=round(float(dividendo_medio_5)/0.08,2)
        df.loc[index,'PRECOTETO_10']=round(float(dividendo_medio_5)/0.1,2)

        df.loc[index,'V/VP']= round(aapl.info['priceToBook'],2)
        df.loc[index,'EV/EBITDA']= round(aapl.info['enterpriseToEbitda'],2) if "enterpriseToEbitda" in aapl.info else 0.0

        

    def lucro_por_preco(self,acao):
        aapl = yf.Ticker(f"{acao}.SA")
        dx= aapl.financials
        ########################################################################################
        lucro_liquido= dx[dx.index.isin(['Net Income'])]
        lucro_liquido =lucro_liquido.transpose()
        lucro_liquido=lucro_liquido.infer_objects(copy=False).fillna(0)# type: ignore
        lucro_liquido.index.name = 'Date'
        lucro_liquido.index= pd.to_datetime(lucro_liquido.index).date
        ########################################################################################
        dp=aapl.history(period="5y").reset_index()
        dp['Date'] = pd.to_datetime(dp['Date'])
        dp=dp.resample(on="Date", rule="ME").max().reset_index(drop=False)
        dp['year'] = dp['Date'].dt.year
        dp['month'] = dp['Date'].dt.month
        dp['Date'] =  dp['Date'].dt.date
        dp1 = dp[dp['month']==12]
        # dp1.loc[:, ['Close']] =dp1['Close'] * 10000000
        dp2 = dp1[['Date','Close']].set_index(['Date'])
        ########################################################################################
        dx=pd.concat([dp2,lucro_liquido],axis=1 ).reset_index()
        dx=dx.infer_objects(copy=False).fillna(0) # type: ignore
        dx.rename(columns={'index': 'Data', 'Close': 'Preco','Net Income':'Lucro'}, inplace=True)
        dx.sort_values(['Data'], ascending=[False])

        fig, ax1 = plt.subplots(1,1,num=acao)
        dx.Preco.plot(ax=ax1, color='blue', label='Preco')
        ax2 = ax1.twinx()
        dx.Lucro.plot(ax=ax2, color='green', label='Lucro')
        ax1.set_ylabel('Preco')
        ax2.set_ylabel('Lucro')
        ax1.legend(loc=3)
        ax2.legend(loc=0) # type: ignore
        ax1.set_xticklabels(dx.Data)
        ax1.set_xticks(np.arange(len(dx.Data)))
        # plt.savefig(f'{acao}.png')

    def GRAFICO(self,dx,tag):
        dx.plot(kind="bar",x="ACAO",y=['PRECO','VALOR_COMPRA'])
        # plt.show()
        plt.savefig(f'{tag}.png')

CARTEIRA = {
    "CXSE3":500,
    "BBSE3":0,
    "BBAS3":1500,
    "TAEE11":600,
    "UNIP6":0,
    "TRPL4":0,
    "VALE3":600,
    "BBDC4":0,
    "SAPR11":0,
    "CSMG3":0,
    "SANB11":0,
    "ITSA4":0,
    "CMIG4":0
}

# CARTEIRA = {
#     "CXSE3":500
# }
ACOES = list(CARTEIRA.keys())
VALORES = list(CARTEIRA.values())
# VALORES = [1000 for x in range(0,9)]
valor_prospectado = 30000
valor_disponivel = 6000 #float(input("Digite Valor Total Disponivel: "))
ACAO(valor_prospectado,ACOES,VALORES,valor_disponivel).start()
# # ACAO(valor_aplicado,ativos,CARTEIRA).lucro_por_preco("TRPL4")



