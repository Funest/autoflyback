# Imports
import subprocess
import re
import os
import ltspice
import time
import multiprocessing as mltp
from pathlib import Path

# Localização padrão do LTspice (modificar a variável se for outro local)
ltspice_exe_path = os.path.expanduser("~/AppData/Local/Programs/ADI/LTspice/LTspice.exe")

class projetoLT:
    # asc = caminho até o arquivo .asc da simulação
    def __init__(self, asc: str):
        self.asc = asc
        self.asc_old = asc
        self.raw = self.asc.replace(".asc", ".raw")
        if not os.path.exists(self.asc):
            print(f"Alerta: Arquivo '{self.asc}' não existe. Tem certeza que está correto?")
        if os.path.exists(self.raw):
            self.resultado = ltspice.Ltspice(self.raw)
            self.executado = True
        else:
            self.resultado = []
            self.executado = False

    # Descrição do arquivo .asc e se foi executado
    def __str__(self):
        if self.executado:
            executext = "executado"
        else:
            executext = "não executado"
        if not os.path.exists(self.asc):
            nome_proj = self.asc
        else:
            nome_proj = f"{os.path.basename(self.asc).replace(".asc", "")} ({self.asc})"
        return f"{nome_proj}, {executext}."
    
    def abrir(self):
        subprocess.run([ltspice_exe_path, self.asc])
    
    def executar(self):
        resultado = somenteExecutar(self.asc)
        self.executado = True
        if not self.resultado:
            self.resultado = resultado
        self.resultado.parse()

    # Duas coisas necessárias para modificar um dispositivo:
    # - Nome da instância (InstName); e
    # - Valor do principal parâmetro (Value)
    # Parâmetros (Nome=Valor):
    # - Nome; e 
    # - Valor
    # Solução: dicionario[nome] = valor
    def novoAsc(self, dispositivos:dict={}, parametros:dict={}, sufixo:str="_new", new_path:str=None):
        asc_file_handle = open(self.asc_old, "r")
        new_file = self.asc_old.replace(".asc", sufixo + ".asc")
        if new_path:
            filename = os.path.basename(new_file)
            new_file = f'{new_path}/{filename}'
            Path(new_path).mkdir(parents=True, exist_ok=True)
        new_asc_handle = open(new_file, "w")
        searchPatternInstName = rf"^SYMATTR\s+InstName\s+(\S+)\s*$"
        searchPatternParam = rf"^TEXT.*?\.param.*?$"
        for linha in asc_file_handle:
                padrao_inst = re.match(searchPatternInstName, linha)
                padrao_param = re.match(searchPatternParam, linha)
                if padrao_inst and (padrao_inst.group(1) in dispositivos.keys()):
                    new_asc_handle.write(linha)
                    prox_linha = next(asc_file_handle)
                    padrao_value = re.match(r'^SYMATTR\s+Value', prox_linha)
                    newValueLine = f"SYMATTR Value {dispositivos[padrao_inst.group(1)]}\n"
                    new_asc_handle.write(newValueLine)
                    if not padrao_value:
                        new_asc_handle.write(prox_linha)
                        
                elif padrao_param:
                    nova_linha = linha
                    for par in parametros.keys():
                        nova_linha = re.sub(fr"{par}=\S+", f"{par}={parametros[par]}", nova_linha)
                    new_asc_handle.write(nova_linha)
                else:
                    new_asc_handle.write(linha)
        asc_file_handle.close()
        new_asc_handle.close()
        return new_file
    
    def modificar(self, dispositivos:dict={}, parametros:dict={}, sufixo:str="_new"):
        new_asc = self.novoAsc(dispositivos, parametros, sufixo)
        self.asc = new_asc
        self.raw = new_asc.replace(".asc", ".raw")
        self.resultado = []
        self.executado = False

    # Dado um dicionário[dispositivo] = [val1, val2, ...], executa n_proc simulações em paralelo,
    #   a fim de reduzir o tempo de uma batelada de simulações
    #   retorna uma lista de Ltspice do pacote ltspice
    def processamentoParalelo(self, n_proc:int, dispositivos:dict={}, parametros:dict={},
                              sufixo:str='_new', new_path:str=None, quiet=False) -> ltspice.Ltspice:
        arquivos, status = self.gerarModificados(dispositivos, parametros, sufixo, new_path=new_path, quiet=quiet)
        if not status:
            print("Algo deu errado. Abortando.")
            return
        return executarParalelo(arquivos, n_proc)

    def processamentoBatelada(self, dispositivos:dict={}, parametros:dict={},
                              sufixo:str='_new', new_path:str=None, quiet=False) -> ltspice.Ltspice:
        arquivos, status = self.gerarModificados(dispositivos, parametros, sufixo, new_path=new_path, quiet=quiet)
        if not status:
            print("Algo deu errado. Abortando.")
            return
        return executarBatelada(arquivos)
    
    def gerarModificados(self, dispositivos:dict={}, parametros:dict={}, sufixo='_new', 
                         new_path:str=None, quiet=False):
        ## Obtém o tamanho dos elementos dos dicionários e acusa um erro se diferirem 
        # (-1 é usado para o dicionario vazio), o qual é permitido para apenas uma das entradas de cada vez
        def tamanhoUnanime(dicionario:dict):
            size = -1
            for key in dicionario:
                size_i = len(dicionario[key])
                if size < 0:
                    size = size_i
                elif size != size_i:
                    return 0
            return size
    
        tam_disps = tamanhoUnanime(dispositivos)
        tam_param = tamanhoUnanime(parametros)

        if not tam_disps or not tam_param or ((tam_disps > 0 and tam_param > 0) and tam_disps != tam_param):
            print(f'Erro: Número de valores para cada parâmetro e dispositivo diferem ou são itens vazios. Abortando.')
            return [], False
        elif (tam_disps < 0 and tam_param < 0):
            print(f"Erro: Nada a modificar. Abortando.")
            return [], False
        
        # Se nenhum for -1, são iguais, N1 = N2 = N > 0, então max(N1, N2) = N
        # Se um for -1, e o outro é N > 0 > -1, então max(N, -1) = N
        # Ambos sendo -1 são pegos no elif acima, e N != -1 nunca é negativo pois vem de len(.)
        # N1 != N2 > 0 é pego no if acima
        numero_valores = max(tam_disps, tam_param)
        ## Fim da verificação de tamanhos
        if not quiet:
            print('----------------------------------------')
            print('Arquivos gerados:')
        ascs = []
        for k in range(numero_valores):
            disp_k = {key: dispositivos[key][k] for key in dispositivos}
            param_k = {key: parametros[key][k] for key in parametros}
            suf_k = sufixo + f'_{k}'
            asc_novo = self.novoAsc(disp_k, param_k, suf_k, new_path=new_path)
            ascs.append(asc_novo)
            if not quiet:
                print(f'\t-> {asc_novo}:\n\t\t{disp_k}\n\t\t{param_k}')
        if not quiet:
            print('----------------------------------------')

        return ascs, True

        

# Função para encontrar o Duty Cycle necessário para uma saída específica:
# Realiza uma busca binária no intervalo (D_max, D_min), partindo de D_ini, 
#   por um D tal que |V(vo) - Vo_alvo| < epsilon, com máximo de max_iters
# MODIFICA proj, o qual deve aceitar um parâmetro (padrão D) que modifique a saída (padrão V(vo))
# Parâmetros adicionais:
#   - D_name: Nome do parâmetro do duty cycle
#   - vo_name: Medição de saída
#   - quiet: Verdadeiro se não quiser saídas no terminal
#   - direcao: 1 se a saída cresce com D, -1 se decresce
# Saídas:
#   - Vo: a saída final
#   - D: o duty cycle final
#   - status: True se o processo convergiu, False caso contrário

def otimizarDuty(proj:projetoLT, D_ini:float, D_max:float, 
                 D_min:float, Vo_alvo:float, epsilon:float, max_iters:int,
                 quiet:bool = False, vo_name:str='V(vo)', D_name:str='D', direcao=1):
    inicio_proc = time.time()
    D = D_ini
    for i in range(max_iters):
        print(f'Iteração {i + 1}: D = {D:.6f}') if not quiet else None
        inicio_iter = time.time()
        pars = {D_name: f'{D:.6f}'}
        novo_asc = proj.novoAsc({}, pars, sufixo="_D")
        saida = somenteExecutar(novo_asc, quiet=True)
        fim_iter = time.time()
        print(f'Demorou {fim_iter - inicio_iter:.2f} s, total {fim_iter - inicio_proc:.2f} s') if not quiet else None
        saida.parse()
        vo_vec = saida.get_data(vo_name)
        Vo = vo_vec.mean()
        eVo = Vo - Vo_alvo
        print(f'Vo = {Vo} V, eVo = {eVo} V') if not quiet else None
        if abs(eVo) < epsilon:
            print('Atingido.') if not quiet else None
            break
        elif direcao*Vo > direcao*Vo_alvo:
            D_max = D
            D = (D_min + D)/2
        else:
            D_min = D
            D = (D_max + D)/2
        print(f'Novo D = {D:.6f}') if not quiet else None
    fim_proc = time.time()
    print(f'Tempo total: {fim_proc - inicio_proc:.2f} s') if not quiet else None
    if (abs(eVo) > epsilon):
        print('Não foi possível atingir o Vo desejado.') if not quiet else None
        print(f'Vo = {Vo} V, eVo = {eVo} V = {eVo/Vo*100:.2f} %') if not quiet else None
        status = False
    else: status = True
    return novo_asc, Vo, D, status, i+1

def executarParalelo(arquivos:list[str], n_proc):
    with mltp.Pool(processes=n_proc) as pool:
        return pool.map(somenteExecutar, arquivos)

def executarBatelada(arquivos:list[str]):
    resultados = []
    for asc in arquivos:
        resultados.append(somenteExecutar(asc))
    return resultados
        
def somenteExecutar(nome_asc:str, quiet=False):
    nome_raw = nome_asc.replace('.asc', '.raw')
    subprocess.run([ltspice_exe_path, "-b", "-Run", nome_asc])
    print(f'Processado {nome_asc}.') if not quiet else None
    return ltspice.Ltspice(nome_raw)
