## Imports
import numpy as np
from matplotlib import pyplot as plt
from pathlib import Path

## Funções
def curva_pareto(objetivos:np.ndarray):
    # objs: nxm: n pontos x m funções objetivo.
    # encontra os pontos não dominados sob os objetivos
    n_pontos = objetivos.shape[0]
    mascara = np.ones(n_pontos, bool)
    for i in range(n_pontos):
        for i2 in range(i+1, n_pontos): 
            # supostamente todo número abaixo de i já checou com ele
            if max(objetivos[i] - objetivos[i2]) < 0:
                # Se alguém dominar esse projeto
                mascara[i] = False
            elif max(objetivos[i2] - objetivos[i]) < 0:
                mascara[i2] = False
    
    return mascara

## Definição de caminhos e leitura de arquivos
class Projeto:
    def __init__(self, num:int, Vo:float, Pin:float, Pout:float, Pdiodo:float,
                 Pmosfet:float, Prclamp:float, Prdamp:float):
        self.num = num
        self.Vo = Vo
        self.Pin = Pin
        self.Pout = Pout
        self.Pdiodo = Pdiodo
        self.Pmosfet = Pmosfet
        self.Prclamp = Prclamp
        self.Prdamp = Prdamp
        self.obter_dispositivos()
        self.obter_metricas()

    def obter_dispositivos(self):
        info = legenda[self.num]
        self.fs = info[1]*1e3
        self.Nucleo = info[2]
        self.Mosfet = info[3]
        self.Diodo = info[4]

        self.volMos = vol_encapsulamentos[encapsulamento_disps[self.Mosfet]]
        self.volDio = vol_encapsulamentos[encapsulamento_disps[self.Diodo]]
        self.volNuc = vol_nucleos[self.Nucleo]
        self.perdaNuc = wl_nucleos[self.Nucleo]
    
    def obter_metricas(self):
        self.dp = self.Pout/(self.volDio+self.volMos+self.volNuc)
        self.eff = self.Pout/(self.Pin+self.perdaNuc)

base_exemplo = Path('exemplos/flyback')
base_saidas = base_exemplo / 'saidas'
base_entradas = base_exemplo / 'entradas'

tabela = np.loadtxt(base_saidas / 'tabela.csv', delimiter=',')
legenda = np.loadtxt(base_saidas / 'legenda.csv', delimiter=',',
                     dtype="int,int,U32,U32,U32")

vol_encapsulamentos = {data[0]: data[1]*data[2]*data[3] for data in 
                       np.loadtxt(base_entradas / 'encapsulamentos.csv',
                                  delimiter=',', dtype="U32,float,float,float",
                                  skiprows=1)}

encapsulamento_disps = {data[0]: data[1] for data in 
                        np.loadtxt(base_entradas / 'mosfets.csv',
                                   delimiter=',', dtype=str, skiprows=1,
                                   usecols=(0, 10))}
encapsulamento_disps |= {data[0]: data[1] for data in 
                         np.loadtxt(base_entradas / 'diodos.csv',
                                    delimiter=',', dtype=str, skiprows=1,
                                    usecols=(0, 7))}

vol_nucleos:dict[float] = {}
wl_nucleos:dict[float] = {}
for data in np.genfromtxt(base_entradas / 'indutores.csv', delimiter=',', 
                          dtype='U32,float,float', usecols=(0, 6, 8)):
    if not np.isnan(data[1]):
        wl_nucleos[data[0]] = data[1]
        vol_nucleos[data[0]] = data[2]

projetos = [Projeto(int(item[0]), item[1], abs(item[2]), item[3], 
                    item[4], item[5], item[6], item[7]) 
                    for item in tabela]

# Matriz de projetos n_freq x n_proj/n_freq, para produzir o scatter
proj2d = []
for freq in [20e3, 40e3, 60e3, 80e3, 100e3]:
    proj_f = []
    for projeto in projetos:
        if projeto.fs == freq:
            proj_f.append(projeto)
    proj2d.append(proj_f)

## Curva pareto e ótimos
objetivos = np.asarray([[proj.eff, proj.dp] for proj in projetos])
masc = curva_pareto(objetivos)
projetos_pareto = np.asarray(projetos)[masc]

# Eficiências e densidades de potência
dp = np.array([proj.dp*1000 for proj in projetos_pareto])
eff = np.array([proj.eff*100 for proj in projetos_pareto])

# Ótimos para cada objetivo
idx = np.argsort(dp)
dp_sort = dp[idx]
eff_sort = eff[idx]
projetos_pareto_sort = projetos_pareto[idx]
mais_eff = projetos_pareto_sort[0]
mais_denso = projetos_pareto_sort[-1]

# Solução de compromisso:
#   Maior valor do produto normalizado dos objetivos
dp_normal = dp - dp.min()
dp_normal = dp_normal/dp_normal.max()

eff_normal = eff - eff.min()
eff_normal = eff_normal/eff_normal.max()

idx_comp = np.argmax(dp_normal*eff_normal)
compromisso = projetos_pareto[idx_comp]

## Gráfico
fig, ax = plt.subplots()

# Scatter total, separados por frequência (uma chamada de .plot por frequência)
i = 0
mark = ['x', 'o', '^', 's', '+']
freqs = range(20, 101, 20)
for freq in proj2d:
    effs = [proj.eff*100 for proj in freq]
    dp = [proj.dp*1000 for proj in freq]
    ax.plot(dp, effs, 'k' + mark[i], label=f'{freqs[i]} kHz',
             fillstyle='none')
    i+=1

# Primeira legenda
leg1 = ax.legend(loc='upper right')
ax.add_artist(leg1)

# Desenho da curva de pareto e soluções selecionadas
pareto, = ax.plot(dp_sort, eff_sort, 'r:*', lw=2, label='Fronteira Pareto', ms=10, fillstyle='none')

opt_dp = [proj.dp*1000 for proj in [mais_eff, compromisso, mais_denso]]
opt_eff = [proj.eff*100 for proj in [mais_eff, compromisso, mais_denso]]
opt, = ax.plot(opt_dp, opt_eff, 'b*', lw=2, ms=15, label='Projetos selecionados')

ax.legend(handles=[pareto, opt], loc='lower left')

# Eixos e grade
ax.set_ylabel('Rendimento [%]')
ax.set_xlabel('Densidade de potência [mW/mm$^3$]')
ax.minorticks_on()
ax.grid(which='minor', ls='--', lw=0.25)
ax.grid(which='major', lw=0.5)

# Relatório das soluções selecionadas
relatorio = f"""Mais eficiente: {mais_eff.num} a {mais_eff.fs//1e3} kHz, com núcleo {mais_eff.Nucleo}, mosfet {mais_eff.Mosfet}, diodo {mais_eff.Diodo}
\tdp = {mais_eff.dp*1000:.2f} mW/mm³, eff = {mais_eff.eff*100:.3f} %
Mais denso: {mais_denso.num} a {mais_denso.fs//1e3} kHz, com núcleo {mais_denso.Nucleo}, mosfet {mais_denso.Mosfet}, diodo {mais_denso.Diodo}
\tdp = {mais_denso.dp*1000:.2f} mW/mm³, eff = {mais_denso.eff*100:.3f} %
Solução de compromisso: {compromisso.num} a {compromisso.fs//1e3} kHz, com núcleo {compromisso.Nucleo}, mosfet {compromisso.Mosfet}, diodo {compromisso.Diodo}
\tdp = {compromisso.dp*1000:.2f} mW/mm³, eff = {compromisso.eff*100:.3f} %"""

print(relatorio)

saida = open(base_saidas / 'otimos.txt', 'w', encoding='utf-8')
saida.write(relatorio)
saida.close()

# Salvamento da figura
fig.savefig(base_saidas / 'pareto.png', bbox_inches='tight')
fig.savefig(base_saidas / 'pareto.pdf', bbox_inches='tight')
plt.show()
