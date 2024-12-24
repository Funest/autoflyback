## Calcula os componentes passivos e cria os .ascs de acordo com a informação nos csvs na pasta entrada/
##   Salvando os ascs gerados na pasta pipeline/ (pasta de arquivos transitórios) 
##   Salva também uma legenda (em .txt e em .csv) na pasta saidas/

import sys

# Raiz do repositório para acessar os scripts
sys.path.append('.')

from dataclasses import dataclass
from pathlib import Path
import numpy as np
import autolts.autolts as alts

@dataclass
class Indutor:
    fs: float
    Nucleo: str
    N1: int
    N2: int
    L1: float
    L2: float
    Wloss: float
    Vol: float

@dataclass
class Mosfet:
    Nome: str
    Vbreakdown: float
    Coss: float
    Encapsulamento: str

@dataclass
class Diodo:
    Nome: str
    Encapsulamento: str

prefixos_ltspice = ["f", "p", "n", "u", "m", "", "k", "Meg", "G", "T"]
def pretty_print(numero:float) -> str:
    if numero == 0:
        return '0'
    log1000 = int(np.log10(abs(numero))//3)
    idx = log1000+5
    if idx >= len(prefixos_ltspice):
        idx = len(prefixos_ltspice) - 1
        log1000 = 4
    elif idx < 0:
        idx = 0
        log1000 = -5
    numero_corrigido = numero * 1e-3**log1000
    return f'{numero_corrigido:g}{prefixos_ltspice[log1000+5]}'

base_exemplo = Path('exemplos/flyback')
base_entradas = base_exemplo / 'entradas'
base_pipeline = base_exemplo / 'pipeline'
base_saida = base_exemplo / 'saidas'
base_pipeline.mkdir(exist_ok=True)
base_saida.mkdir(exist_ok=True)

diodo_dados = np.loadtxt(base_entradas / 'diodos.csv', usecols=(0,7),
                 skiprows=1, delimiter=',', dtype=str)
mosfet_dados = np.loadtxt(base_entradas / 'mosfets.csv', usecols=(0,2,8,10),
                 skiprows=1, delimiter=',', dtype="|U32,float,float,|U32")

indutores: list[Indutor] = []
linha_cabecalho_fs = [1, 6, 11, 16, 21]
for fs, i in zip([20e3, 40e3, 60e3, 80e3, 100e3], range(5)):
    indutores_fs = np.loadtxt(base_entradas / 'indutores.csv', usecols=(0,1,2,3,4, 6, 8),
                              skiprows=2 + 5*i, max_rows=2, delimiter=',',
                              dtype="U32,int,int,float,float,float,float")
    indutores += [Indutor(fs, ind[0], ind[1], ind[2], ind[3]*1e-6,
                             ind[4]*1e-6, ind[5], ind[6]) for ind in indutores_fs]

diodos = [Diodo(dado[0], dado[1]) for dado in diodo_dados]
mosfets = [Mosfet(dado[0], dado[1], dado[2]*1e-12, dado[3]) for dado in mosfet_dados]

Nd = len(diodos)
Nm = len(mosfets)
Ni = len(indutores)
Nt = Nm*Nd*Ni

# print(f'{Ni} (indutores * frequencias) x {Nd} diodos x {Nm} mosfets = {Nt} simulações')
# ts = 30 
# print(f'Com {ts} s por simulação: {Nt*ts} s = {Nt*ts/60} min = {Nt*ts/3600} h')

# Ni2 = 2*5
# Nt2 = Nm*Nd*Ni2
# print(f'Com 2 indutores por frequência: {Nt2*ts} s = {Nt2*ts/60} min = {Nt2*ts/3600} h')

# Nm2 = 10
# Nt3 = Nm2*Nd*Ni2
# print(f'\t Com somente 10 mosfets: {Nt3*ts} s = {Nt3*ts/60} min = {Nt3*ts/3600} h')

# Nd4 = 5
# Nm4 = 5
# Nt4 = Nm4*Nd4*Ni2
# print(f'\t Com 2 indutores por frequência, 5 mosfets e 5 diodos: {Nt4*ts} s = {Nt4*ts/60} min = {Nt4*ts/3600} h')


#### Especificação da fonte
especificacoes = {
    'Vo': 150,
    'Dvo': 150*0.01,
    'Po': 100,
    'Emax': 72,
    'D': 0.45
}
proj = alts.projetoLT(str(base_entradas / 'flyback_ma.asc'))

#### Definições de tolerâncias e estimativas
# Il1_leak/Il1_m
leak = 0.02
# Mosfet
margem_breakdown = 0.85
# Capacitor de saída
esr_Co_esperada = 0.01
# Desempenho
eff = 0.8 # eficiência esperada
# Amortecimento
Q = 1.5

# Coisas da legenda
legenda = open(base_saida / 'legenda.txt', 'w')
legendacsv = open(base_saida / 'legenda.csv', 'w')
tam_Nt = max(len(str(Nt-1)), len('#Simulacao'))
tam_fs = max(len(str(int(max([ind.fs for ind in indutores])/1e3))), len('fs (kHz)'))
tam_nucnome = max(max([len(ind.Nucleo) for ind in indutores]), len('Nucleo'))
tam_mosnome = max(max([len(mos.Nome) for mos in mosfets]), len('Mosfet'))
tam_dionome = max(max([len(dio.Nome) for dio in diodos]), len('Diodo'))

linha_legenda = f'{'#Simulacao'.ljust(tam_Nt)} '
linha_legenda += f'{'fs (kHz)'.ljust(tam_fs)} '
linha_legenda += f'{'Nucleo'.ljust(tam_nucnome)} '
linha_legenda += f'{'Mosfet'.ljust(tam_mosnome)} '
linha_legenda += f'{'Diodo'.ljust(tam_dionome)}\n'

linha_legendacsv = '#Simulacao,'
linha_legendacsv += 'fs (kHz),'
linha_legendacsv += 'Nucleo,'
linha_legendacsv += 'Mosfet,'
linha_legendacsv += 'Diodo\n'

legenda.write(linha_legenda)
legendacsv.write(linha_legendacsv)

i=0
for ind in indutores:
    #### Grandezas calculadas
    N1porN2 = float(ind.N1)/ind.N2
    Ip_min = especificacoes['Po']/eff/especificacoes['Emax']
    Vr = especificacoes['Vo'] * N1porN2
    Io = especificacoes['Po']/especificacoes['Vo']
    # Calcula Co
    Dvo_R = esr_Co_esperada * Io * (1+especificacoes['D'])/(1-especificacoes['D'])

    if Dvo_R >= especificacoes['Dvo']:
        print('Não é possível realizar com essa resistência série.')
        print(f'ΔVo no resistor é {Dvo_R:.2e} V = {Dvo_R/especificacoes['Vo']*100:.2} %')
        Co = Io**2 * ( (1+especificacoes['D']) / (1 - especificacoes['D']) / (N1porN2) )**2 * ind.L1 / (2 * especificacoes['Vo'] * (especificacoes['Dvo']))
        print(f'Sem a resistência série, Co = {Co:.3e} F')
    else:
        Co = Io**2 * ( (1+especificacoes['D']) / (1 - especificacoes['D']) / (N1porN2) )**2 * ind.L1 / (2 * especificacoes['Vo'] * (especificacoes['Dvo'] - Dvo_R))
        print(f'Co = {Co:.3e} F')

    for mos in mosfets:
        #### Dimensionamento do circuito de clamp
        L1leak = leak*ind.L1
        Vclamp = mos.Vbreakdown*margem_breakdown - especificacoes['Emax']

        Rclamp = 2*Vclamp*(Vclamp - Vr)/(L1leak * Ip_min**2 * ind.fs)
        Cclamp = Vclamp/((Vclamp-Vr)*Rclamp*ind.fs)



        if Rclamp <= 0 or Cclamp <=0:
            print(f'fs = {ind.fs/1e3} kHz, Núcleo {ind.Nucleo}')
            print(f'Vclamp = {Vclamp} V (Vr = {Vr} V) para mosfet {mos.Nome} !!!')
            Rclamp = 2*Vclamp**2/(L1leak * Ip_min**2 * ind.fs)
            Cclamp = 1/(Rclamp*ind.fs)
        #else:
            #print(f'Circuito de clamp: Rc = {Rclamp} Ohm, Cc = {Cclamp} F')

        #### Dimensionamento do circuito de damp
        f1 = 1/(2*np.pi)/np.sqrt(L1leak*mos.Coss)

        Rdamp = 2*np.pi*f1*L1leak/Q
        Cdamp = 1/(2*np.pi*f1*Rdamp)

        #print(f'Circuito de damp: Rd = {Rdamp} Ohm, Cd = {Cdamp} F')

        for dio in diodos:
            # Criação dos ascs
            disps = {'L1': pretty_print(ind.L1), 
                    'L2': pretty_print(ind.L2),
                    'Co': pretty_print(Co),
                    'Cc': pretty_print(Cclamp),
                    'Cd': pretty_print(Cdamp),
                    'Rc': pretty_print(Rclamp),
                    'Rd': pretty_print(Rdamp),
                    'D1': dio.Nome,
                    'M1': mos.Nome}
            params = {'fs': f'{ind.fs*1e-3}k'}
            asc = proj.novoAsc(disps, params, new_path=base_pipeline,
                               sufixo=("_new" + f"_{i}"))
            
            # Produção da legenda
            numnome = str(i).ljust(tam_Nt, ' ')
            fsnome = str(int(ind.fs/1e3)).ljust(tam_fs, ' ')
            nucnome = ind.Nucleo.ljust(tam_nucnome, ' ')
            mosnome = mos.Nome.ljust(tam_mosnome, ' ')
            dionome = dio.Nome.ljust(tam_dionome, ' ')
            legenda.write(f'{numnome} {fsnome} {nucnome} {mosnome} {dionome}\n')
            legendacsv.write(f'{str(i)},{str(int(ind.fs/1e3))},{ind.Nucleo},{mos.Nome},{dio.Nome}\n')
            i+=1

#### Dimensionamento do capacitor de saída
# https://www.ti.com/lit/an/slyt800b/slyt800b.pdf?ts=1734371306929&ref_url=https%253A%252F%252Fwww.google.com%252F
# L2\Delta{i} = Vo \Delta{t} <- L2 descarregando na saída
# Considerando \Delta{t} o período em que o capacitor está descarregando,
# O capacitor descarrega quando I_L2 < Io, então integramos entre o início
#   do carregamento e quando ele chega a Io:
# L2*(IL2_pk - Io) = Vo \Delta{t}
# \Delta{t} = L2 * (Il2_pk - Io)/Vo

# Então, no capacitor, \Delta{vo} = Ic_pk * \Delta{t}/(2*C)
#   pois a corrente é triangular nesse período, e Ic_pk = Il2_pk - Io
# Então \Delta{vo} = (Il2_pk - Io)^2 * L2/(2*Vo*C)
#                  = (Il2_pk - Io)^2 * (N1/N2)^{-2} * L1 /(2*Vo*C)

# Il2_pk = (Io * 2)/d'
# Il2_pk - Io = (2/d' - 1) Io = (2 - d') / d' * Io
# se d' for aproximadamente 1 - d,
# Il2_pk - Io ~ (1 + d)/(1-d) * Io

# Então \Delta{vo} = Io^2 * (1 + d)^2/(1-d)^2 (N1/N2)^-2 * L1 / (2 * Vo * C)
# E, finalmente,
#   C = Io^2 * (1+d)^2/(1-d)^2 * (N1/N2)^-2 * L1 / (2 * Vo * \Delta{Vo})
# Como há uma resistência no capacitor, na verdade
#   C = Io^2 * (1+d)^2/(1-d)^2 * (N1/N2)^-2 * L1 / 
#           (2 * Vo * (\Delta{Vo} - rc * Io * (1+d)/(1-d))
