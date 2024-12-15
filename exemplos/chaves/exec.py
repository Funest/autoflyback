# Testa o circuito para cada par de chaves, calculando as potências e eficiência obtidas

# Imports
import sys

# Raiz do repositório para acessar os scripts
sys.path.append('.')
import autolts.autolts as alts

# Para copiar arquivos
import shutil

import proc

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

def imprimir_potencias(proj:alts.projetoLT):
    Po, Pi, Pt, Pd = potencias(proj) 
    eff = Po/Pi
    print(f'Potência de saída: {Po:.2f} W')
    print(f'Potência de entrada: {Pi:.2f} W, eficiência {eff * 100:.2f} %')
    print(f'Perdas: Transistor: {Pt:.2f} W, Diodo: {Pd:.2f} W')
    return Po, eff

# Declaração do projeto
base = "./exemplos/chaves"
boost = alts.projetoLT(f"{base}/LTspice/boost.asc")

class Resultado:
    def __init__(self, chaves:list[proc.Dispositivo], eficiencia:float, dens_pot:float):
        self.chaves = chaves
        self.eficiencia = eficiencia
        self.dens_pot = dens_pot
        self.preco = sum([S.preco for S in chaves])

eff_max = 0
simulacoes:list[Resultado] = []
proc.ler_encapsulamentos(f"{base}/entradas/encapsulamentos")
transistores = proc.ler_dispositivos(f"{base}/entradas/mosfets", False)
diodos = proc.ler_dispositivos(f"{base}/entradas/diodos", False)
for T in transistores:
    for D in diodos:
        disps = {'M1': T.nome, 'D1': D.nome}
        boost.modificar(disps)
        print(f"{T.nome}, {D.nome}")
        boost.executar()
        Po, eff = imprimir_potencias(boost)
        if T.volume and D.volume:
            dp = Po/(T.volume + D.volume)
            print(f'Densidade de potência: {dp} W/mm^3')
        else:
            dp = 0
        if eff > eff_max:
            eff_max = eff
            D_max = D
            T_max = T
            shutil.copyfile("./exemplos/chaves/LTspice/boost_new.asc", "./exemplos/chaves/LTspice/boost_max.asc")
        simulacoes.append(Resultado([D, T], eff, dp))
        

print(f"Máxima eficiência: {eff_max*100:.2f} %, com {T_max.nome} e {D_max.nome}")

from matplotlib import pyplot as plt

for S in simulacoes:
    plt.figure(0)
    plt.scatter(S.dens_pot, S.eficiencia, marker='x')
    plt.figure(1)
    plt.scatter(S.dens_pot, S.preco, marker='x')
    plt.figure(2)
    plt.scatter(S.preco, S.eficiencia, marker='x')
    
plt.figure(0)
plt.xlabel("Densidade de potência [W/mm3]")
plt.ylabel("Eficiência")

plt.figure(1)
plt.xlabel("Densidade de potência [W/mm3]")
plt.ylabel("Preço [USD]")

plt.figure(2)
plt.xlabel("Preço [USD]")
plt.ylabel("Eficiência")

plt.show()