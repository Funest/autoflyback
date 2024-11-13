# Obtém o duty cycle para o ponto de operação desejado em um conversor Boost, 
# e determina a eficiência e as perdas

# Imports
import sys

# Raiz do repositório para acessar os scripts
sys.path.append('.')

import autolts.autolts as alts

# Calculo das potências de entrada, saída e perdas nas chaves no boost
def potencias(proj:alts.projetoLT):
     vo = proj.resultado.get_data('V(vo)')
     v1 = proj.resultado.get_data('V(n001)')
     v2 = proj.resultado.get_data('V(n002)')
     iR = proj.resultado.get_data('I(R2)')
     itd = proj.resultado.get_data('Id(M1)')
     iV1 = proj.resultado.get_data('I(V1)')
     id = proj.resultado.get_data('I(D1)')
     Po = (vo*iR).mean() # Saída
     Pi = -(v1*iV1).mean() # Entrada (negativo pela convenção passiva)
     Pt = (v2*itd).mean() # Transistor (não contando no Gate)
     Pd = ((v2-vo)*id).mean() # Diodo
     return Po, Pi, Pt, Pd

# Declaração do projeto
boost = alts.projetoLT("./exemplos/eficiencia/LTspice/boost.asc")

# Parâmetros para busca
D_ini = 0.3
D_max = 0.5
D_min = 0.1
epsilon = 1.5 # Em volts
max_iters = 10
Vo_alvo = 150

# Obter duty cycle necessário
Vo, D, st = alts.otimizarDuty(boost, D_ini, D_max, D_min, Vo_alvo, epsilon, max_iters)
print('------ fim da busca ------\n')

# Verificação do ripple de saída
vo = boost.resultado.get_data('V(vo)')
dVo = vo.max() - vo.min()
dVo_alvo = 0.01*Vo_alvo

if dVo > dVo_alvo:
    print("dVo VIOLADO!!!")
print(f"dVo = {dVo:.2e} V = {100*dVo/Vo:.2f} %\n")

# Obter potências:
Po, Pi, Pt, Pd = potencias(boost) 
eff = Po/Pi 
print(f'Duty cycle: {D*100:.2f} %, Vo = {Vo:.2f} V')
print(f'Potência de saída: {Po:.2f} W')
print(f'Potência de entrada: {Pi:.2f} W, eficiência {eff * 100:.2f} %')
print(f'Perdas: Transistor: {Pt:.2f} W, Diodo: {Pd:.2f} W')
