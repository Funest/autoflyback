# Imports
import subprocess
import re
import os
import ltspice

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
                    newValueLine = f"SYMATTR Value {dispositivos[padrao_inst.group(1)]}\n"
                    new_asc_handle.write(newValueLine)
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
        self.resultado = ltspice.Ltspice(self.raw)
        self.executado = False