## Executa cada um dos ascs na pasta pipeline/
##   encontrando o duty cycle certo (*_D.asc), gerando os raws (*_D.raw)
import sys

# Raiz do repositório para acessar os scripts
sys.path.append('.')

import autolts.autolts as alts
from pathlib import Path
import time

base_exemplo = Path('exemplos/flyback')
base_pipeline = base_exemplo / 'pipeline'

ascs = [str(f) for f in list(base_pipeline.glob('*[0-9].asc'))]

inicio = time.time()
its = []
for asc in ascs:
    ltproj = alts.projetoLT(asc)
    novoasc, Vo, _, stat, Ni = alts.otimizarDuty(ltproj, 0.405, 0.5, 0.3,
                                               150, 10, 10,
                                               quiet=True
                                               )
    print(f'{Path(novoasc).name}: Vo = {Vo} V, {Ni} iterações')
    its.append(Ni)
    if not stat:
        print(f'{asc} não convergiu')

fim = time.time()
dt = fim - inicio

print(f'Demorou {dt:.2f} s = {dt/60:.2f} min = {dt/3600:.2f} h')