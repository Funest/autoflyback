import sys

# Raiz do repositório para acessar os scripts
sys.path.append('.')

# import
import autolts.autolts as alts
from matplotlib import pyplot as plt

# funcao para desenhar a saída
fignum = 0
def desenhar(proj:alts.projetoLT):
    # Valores
    lt.resultado.parse()
    t = lt.resultado.get_time()
    vo = lt.resultado.get_data('V(vo)')
    
    # Obtenção do valor médio nos últimos períodos:
    Ts = 20e-6
    D = 0.2
    dT = 1e-6

    idx = t > t[-1] - 5*Ts
    vo_ult = vo[idx]
    vo_med = vo_ult.mean()

    global fignum
    plt.figure(fignum)
    fignum += 1
    plt.plot(t, vo, 'k')
    plt.hlines(vo_med, t[0], t[-1], 'k', linestyles='--')

# Execução do projeto definido no arquivo asc:
lt = alts.projetoLT("./exemplos/modificacao_simples/LTspice/Draft1.asc")
lt.executar()
desenhar(lt)

# Modificações: mudança da chave M1, mudança dos parâmetros D e Ts,
# Os parâmetros estão sendo usados no arquivo .asc para definir o chaveamento
disps = {"M1": 'STN3N45K3'}
pars = {"D": '0.3', "Ts": '1u'}
lt.modificar(disps, pars)
lt.executar()
desenhar(lt)

plt.show()

disps = {"M1": []}

# Abrir o arquivo e ler todas as chaves
with open("./exemplos/modificacao_simples/chaves.txt", "r") as arquivo:
    for linha in arquivo:
        linha = linha.strip()  
        if linha: 
            disps["M1"].append(linha) 

# Iteração de modificação das chaves e seus valores
for id_disp, valores_disp in disps.items():  #
    for valor_disp in valores_disp:  
        disps[id_disp] = valor_disp
        lt.modificar(disps, pars)
        lt.executar()            
        desenhar(lt)             
        plt.savefig(f"{id_disp}_{valor_disp}.png")  
        plt.close()  