# Imports
import subprocess
import re
import os
import ltspice
import time

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
        subprocess.run([ltspice_exe_path, "-b", "-Run", self.asc])
        self.executado = True
        if not self.resultado:
            self.resultado = ltspice.Ltspice(self.raw)
        self.resultado.parse()

    # Duas coisas necessárias para modificar um dispositivo:
    # - Nome da instância (InstName); e
    # - Valor do principal parâmetro (Value)
    # Parâmetros (Nome=Valor):
    # - Nome; e 
    # - Valor
    def modificar(self, dispositivos:dict, parametros:dict={}, sufixo:str="_new"):
        asc_file_handle = open(self.asc_old, "r")
        self.asc = self.asc_old.replace(".asc", sufixo + ".asc")
        new_asc_handle = open(self.asc, "w")
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
        self.raw = self.asc.replace(".asc", ".raw")
        self.resultado = []
        self.executado = False

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
        proj.modificar({}, pars)
        proj.executar()
        fim_iter = time.time()
        print(f'Demorou {fim_iter - inicio_iter:.2f} s, total {fim_iter - inicio_proc:.2f} s') if not quiet else None
        vo_vec = proj.resultado.get_data(vo_name)
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
    if (abs(eVo) > epsilon) and not quiet:
        print('Não foi possível atingir o Vo desejado.')
        print(f'Vo = {Vo} V, eVo = {eVo} V = {eVo/Vo*100:.2f} %')
        status = False
    else: status = True
    return Vo, D, status
