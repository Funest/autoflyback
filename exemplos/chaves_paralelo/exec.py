# Roda uma simulação para cada par de chaves, mas só para testar o tempo necessário

## Imports
import sys

# Raiz do repositório para acessar os scripts
sys.path.append('.')
import autolts.autolts as alts

import proc
import time

# Declaração do projeto
base = "./exemplos/chaves_paralelo"
boost = alts.projetoLT(f"{base}/LTspice/boost.asc")

class Resultado:
    def __init__(self, chaves:list[proc.Dispositivo], eficiencia:float, dens_pot:float):
        self.chaves = chaves
        self.eficiencia = eficiencia
        self.dens_pot = dens_pot
        self.preco = sum([S.preco for S in chaves])

proc.ler_encapsulamentos(f"{base}/entradas/encapsulamentos")
transistores = proc.ler_dispositivos(f"{base}/entradas/mosfets", False)
diodos = proc.ler_dispositivos(f"{base}/entradas/diodos", False)
seq_T = []
seq_D = []
for T in transistores:
    for D in diodos:
        seq_T.append(T.nome)
        seq_D.append(D.nome)

disps = {'M1': seq_T, 'D1': seq_D}

# MUITO IMPORTANTE, COLOCAR CÓDIGO DE MULTIPROCESSAMENTO NESSE IF MAIN:
# CASO CONTRÁRIO, FORK BOMB
if __name__ == "__main__":
    # Pequeno benchmark
    n_proc_vec = range(1,5) # 1 a 4
    times = []
    for n_proc in n_proc_vec:
        antes = time.time()
        for i in range(5):
            resultados = boost.processamentoParalelo(n_proc, disps, new_path=f'{base}/pipeline')
        time_n = (time.time() - antes)/5
        times.append(time_n)
        print(time_n)
    for n_proc, time_n in zip(n_proc_vec, times):
        print(f'{n_proc}: {time_n} s')

# No meu notebook:
#1: 73.80515832901001 s
#2: 45.160546493530276 s <---
#3: 455.5336054325104 s
#4: 2071.77955288887 s
