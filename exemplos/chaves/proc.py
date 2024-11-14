base = "./exemplos/chaves"

enc_vols = {}
def ler_encapsulamentos(arquivo:str):
    global enc_vols
    arq_enc = open(arquivo, "r")
    for linha in arq_enc:
        linha = linha.strip()
        if not linha.startswith('#'):
            lista = linha.split()
            enc_vols[lista[0]] = float(lista[1]) * float(lista[2]) * float(lista[3])
    arq_enc.close()


class Dispositivo:
    def __init__(self, nome:str, encapsulamento:str="", preco:float=0.0):
        self.nome = nome
        self.encapsulamento = encapsulamento
        self.volume = enc_vols[encapsulamento] if encapsulamento else 0
        self.preco = preco
    
    def __str__(self):
        return f'{self.nome}: {self.volume} mm^3, ${self.preco}'

def ler_dispositivos(arquivo:str, somente_nomes:bool=False) -> list[Dispositivo]:
    global enc_vols
    if not somente_nomes and not enc_vols:
        print("Encapsulamentos ainda não carregados, abortando.")
        return None
    arq_dis = open(arquivo, "r")
    disps = []
    for linha in arq_dis:
        linha = linha.strip()
        if not linha.startswith('#'):
            lista = linha.split()
            if somente_nomes:
                disps.append(Dispositivo(lista[0]))
            else:
                if len(lista) < 3:
                    print("Elementos insuficientes para modelo completo. Abortando.")
                    return None
                disps.append(Dispositivo(lista[0], lista[1], float(lista[2])))
    arq_dis.close()
    return disps
