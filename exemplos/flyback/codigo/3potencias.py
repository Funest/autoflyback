## Processa todos os arquivos pipeline/*_D.raw
##   Salva para cada um, o Vout e as potências nos resistores de snubber e amortecimento, nas chaves e de entrada/saída
##   O resultado é escrito em saidas/tabela.csv
import sys

# Raiz do repositório para acessar os scripts
sys.path.append('.')

import autolts.autolts as alts
import ltspice
from pathlib import Path

import scipy as sp

def media_integral(y, t):
    Dt = t[-1] - t[0]
    return sp.integrate.trapezoid(y, x=t)/Dt

base_exemplo = Path('exemplos/flyback')
base_entradas = base_exemplo / 'entradas'
base_pipeline = base_exemplo / 'pipeline'
base_saidas = base_exemplo / 'saidas'

raws = [str(f) for f in list(base_pipeline.glob('*_D.raw'))]

vo_max = -1000
vo_min = +1000
f_vo_max = f_vo_min = ""

Nt = 540

tabela = open(base_saidas / 'tabela.csv', 'w')
tabela.write('#Simulacao,Vo,Pi,Po,Pd,Pt,Prc,Prd\n')
for i in range(Nt):
    raw = str(base_pipeline / f'flyback_ma_new_{i}_D.raw')
    dados = ltspice.Ltspice(raw)
    dados.parse()
    t = dados.get_time()
    # Tensões
    e = dados.get_data('V(e)')
    vo = dados.get_data('V(vo)')

    Vo = media_integral(vo, t)

    vd = dados.get_data('V(vd)')
    vl2 = dados.get_data('V(vl2)')
    vc = dados.get_data('V(vc)')
    vrd = dados.get_data('V(vrd)')

    # Correntes
    iv1 = dados.get_data('I(V1)')
    idm1 = dados.get_data('Id(M1)')
    id1 = dados.get_data('I(D1)')
    iro = dados.get_data('I(R1)')
    irc = dados.get_data('I(Rc)')
    ird = dados.get_data('I(Rd)')

    # Potencias
    Po = media_integral(vo*iro, t)
    Pi = media_integral(e*iv1, t)

    Pt = media_integral(vd*idm1, t)
    Pd = media_integral((vl2 - vo)*id1, t)

    Prc = media_integral((e - vc)*irc, t)
    Prd = media_integral((e - vrd)*ird, t)

    tabela.write(f'{i:03d},{Vo:06.2f},{Pi:011.6f},{Po:010.6f},{Pt:010.6f},{Pd:010.6f},{Prc:010.6f},{Prd:010.6f}\n')

    if Vo > vo_max:
        vo_max = Vo
        f_vo_max = raw
    elif Vo < vo_min:
        vo_min = Vo
        f_vo_min = raw

print(f"Vo ∈ [{vo_min:.2f}, {vo_max:.2f}]")
print(f"{f_vo_min}, {f_vo_max}")