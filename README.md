# autoflyback

Ferramentas para automação do projeto de um conversor Flyback.

## Dependências:

* Python 3;
* [LTspice](https://www.analog.com/en/resources/design-tools-and-calculators/ltspice-simulator.html);
* Módulo python [ltspice](https://pypi.org/project/ltspice/).

## autolts

O arquivo `autolts/autolts.py` define uma classe `projetoLT`, a qual tem métodos para automatizar a modificação, execução e obtenção de resultados de um modelo do LTspice, por meio do formato `.asc`.

### Uso

Suponha que exista um modelo no arquivo `pasta/meu_modelo.asc`. Você inicia a variável usando:

```python
proj = projetoLT('pasta/meu_modelo.asc')
```

#### Métodos
Os principais métodos de interesse são:

* `proj.executar()`: Executa o LTspice no fundo e processa o arquivo `.raw` de saída utilizando o módulo `ltspice`. A variável `proj.resultado` conterá um objeto `ltspice.Ltspice` com os resultados da simulação. Para mais informações, veja a [documentação do módulo](https://pypi.org/project/ltspice/).
* `proj.modificar(dispositivos, parametros={}, sufixo="_new")`: Modifica o arquivo `.asc` (salvando um novo arquivo com o sufixo adicionado, como `pasta/meu_modelo_new.asc` e automaticamente mudando o arquivo a ser simulado). O parâmetro `dispositivos` deve ser um dicionário com as chaves sendo o nome do elemento (`InstName`) e com o valor sendo o novo valor principal (`Value`), com uma quantidade arbitrária de elementos. O parâmetro `parametros` deve ser um dicionário com as chaves sendo o nome dos parâmetros (como se fossem variáveis do spice) a serem modificados e o valor associado, o valor desejado.

#### Exemplo
Suponhamos que gostaríamos de mudar o valor do resistor `R1` para 10 Ω e a fonte `V2` para 20 V, o parâmetro `amp` para `12m` e executar a simulação antes e depois da mudança no modelo `RC.asc`. Um exemplo de código para realizar esse procedimento seria:

```python
projeto = projetoLT('RC.asc')
projeto.executar() # A esse ponto, os resultados podem ser acessados

disps = {"R1": "10", "V2": "20"}
params = {"amp": "12m"}
projeto.modificar(disps, params) # A esse ponto, o novo .asc existe
projeto.executar() # Os resultados novos estarão disponíveis no .raw
```