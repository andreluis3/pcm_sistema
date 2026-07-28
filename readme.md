# PCM_Sistema

## 1. Sobre o projeto

O PCM_Sistema é uma aplicação desenvolvida para monitoramento, análise e visualização de dados relacionados a PCM (Phase Change Material). O projeto tem como objetivo apoiar a compreensão do comportamento térmico de materiais e sistemas, permitindo acompanhar temperaturas, calcular indicadores térmicos e comparar diferentes fontes de medição.

A aplicação reúne funcionalidades de interface desktop, processamento de dados, integração com sensores e visualização em dashboard. Entre os cenários de uso estão a análise térmica, comparação entre sensores, avaliação de desempenho e observação de resultados obtidos a partir de dados coletados por hardware e sistemas computacionais.

## 2. Tecnologias utilizadas

A estrutura atual do projeto combina uma interface desktop com serviços de processamento e integração. As principais tecnologias observadas no código são:

| Categoria | Tecnologias | Observação |
| --- | --- | --- |
| Linguagem principal | Python | Base do sistema e da lógica de negócio |
| Interface gráfica | CustomTkinter | Interface desktop moderna e responsiva |
| API | FastAPI | Camada de serviços para integração e acesso a dados |
| Visualização | Matplotlib, Pandas, NumPy | Geração de gráficos e processamento numérico |
| Comunicação com sensores | PySerial | Leitura de dados via porta serial |
| Requisições HTTP | requests | Comunicação com APIs externas e serviços |
| Banco de dados | MySQL e SQLite | O projeto possui integração com MySQL e persistência local em SQLite |
| Configuração | python-dotenv | Utilizado para configuração de variáveis de ambiente quando aplicável |
| Conexão com banco | mysql-connector-python | Integração com MySQL |

## 3. Banco de dados

O projeto passou por uma evolução de armazenamento local para uma arquitetura mais estruturada. Em sua implementação atual, o repositório mostra uma abordagem híbrida:

- armazenamento local em SQLite para desenvolvimento, testes e funcionamento local;
- integração com MySQL por meio de API e cliente HTTP para cenários mais estruturados e escaláveis;
- uso de repositórios híbridos para tentar priorizar a API/MySQL e, caso necessário, fazer fallback para armazenamento local.

No código, os principais elementos de persistência incluem:

- tabela users para autenticação e usuários;
- tabela experiments para armazenar experimentos;
- tabela thermal_calculations para cálculos térmicos;
- tabela tabela_calculos para compatibilidade com fluxos anteriores de interface.

O arquivo de banco SQLite local utilizado em parte do projeto é:

- database/pcmdata.db

A conexão MySQL observada no código aponta para um ambiente local com host localhost, porta 3306, banco thermacore e usuário root, embora esses valores devam ser ajustados para o ambiente do desenvolvedor.

## 4. Arquitetura do sistema

O projeto está organizado em camadas com responsabilidades bem definidas:

- camada de interface: módulos em interface/ e ui/ para telas, navegação e componentes visuais;
- camada de serviços: pasta services/ com repositórios híbridos, clientes de API e controle de cálculos;
- comunicação com banco: módulos em database/ e backend/ para acesso e persistência;
- integração com sensores: pasta sensor_module/ para comunicação serial, simulação e processamento de dados;
- processamento térmico: pasta pcm_module/ para análise, importação, métricas e cálculos;
- visualização: módulos em ui/ e pcm_module/ para dashboards e gráficos.

Estrutura simplificada do projeto:

```text
PCM_Sistema/
├── backend/              # API FastAPI e endpoints
├── core/                 # componentes de processamento e integração
├── database/             # acesso a dados e modelos de persistência
├── interface/            # telas principais da aplicação desktop
├── pcm_module/           # cálculos, métricas e visualização PCM
├── sensor_module/        # comunicação com sensores e simulação
├── services/             # repositórios, clientes API e lógica de negócio
├── ui/                   # componentes visuais e gráficos
├── main.py               # ponto de entrada da aplicação
├── requirements.txt      # dependências do projeto
└── README.md             # documentação principal
```

## 5. Como instalar o projeto

### Pré-requisitos

Antes de iniciar, certifique-se de ter instalado:

- Python 3.x
- Git
- MySQL Server, caso deseje usar o fluxo com banco relacional
- Ambiente virtual Python

### Clonar o projeto

```bash
git clone <url-do-repositorio>
cd PCM_Sistema
```

### Criar ambiente virtual

No Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

No Linux/macOS:

```bash
python3 -m venv venv
source venv/bin/activate
```

### Instalar dependências

```bash
pip install -r requirements.txt
```

Em alguns ambientes, pode ser necessário atualizar o pip antes da instalação:

```bash
python -m pip install --upgrade pip
```

## 6. Configuração do banco MySQL

O projeto possui integração com MySQL em sua camada de API. No código atual, a configuração de conexão está definida diretamente no módulo de API e deve ser ajustada conforme o ambiente local.

Exemplo de configuração esperada:

```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=
DB_NAME=thermacore
DB_PORT=3306
```

Passos recomendados:

1. Criar um banco de dados no MySQL.
2. Criar um usuário com permissão para esse banco.
3. Ajustar as credenciais no código ou em um arquivo de configuração local.
4. Garantir que o servidor MySQL esteja em execução antes de iniciar a API.

> Não foi encontrado um arquivo .env centralizado no repositório. As configurações de conexão atuais estão embutidas no código e devem ser revisadas pelo desenvolvedor.

## 7. Como executar o sistema

### Executar a aplicação desktop

```bash
python main.py
```

### Executar a API FastAPI

A partir da raiz do projeto:

```bash
uvicorn backend.main_api:app --reload --host 0.0.0.0 --port 8000
```

### Ordem recomendada para execução

1. Iniciar o MySQL, se for usar o fluxo relacional.
2. Iniciar a API.
3. Executar a aplicação principal.

## 8. Entrada de dados e sensores

O sistema é preparado para receber dados de temperatura a partir de diferentes fontes, incluindo sensores e fontes de simulação. O módulo sensor_module implementa componentes para leitura serial, simulação térmica e integração com fluxos de aquisição.

O projeto também faz referência a um repositório externo de aquisição com ESP32:

- https://github.com/andreluis3/sensor-temperature-esp32-with-api-serial-mqtt

Esse repositório é associado ao processo de coleta de temperatura utilizando ESP32, sensores e comunicação via API, Serial e MQTT. Os dados coletados podem ser processados e comparados dentro do PCM_Sistema.

Para visualizar os dados gerados pelo sensor, o fluxo recomendado é:

1. Acessar o repositório indicado acima.
2. Abrir a pasta logs.
3. Consultar os arquivos CSV contendo os registros de temperatura.

## 9. Monitoramento da temperatura do computador

O projeto também faz referência a uma integração com o repositório de monitoramento térmico do computador:

- https://github.com/andreluis3/pc_temperature

Esse repositório permite coletar informações térmicas de componentes do computador e comparar esses dados com as medições do sensor ESP32. Esse tipo de comparação pode apoiar análises relacionadas a:

- temperatura ambiente;
- temperatura de componentes;
- desempenho computacional;
- eficiência térmica;
- comparação entre fontes de medição.

## 10. Fluxo de funcionamento

```text
Sensor ESP32
↓
Coleta de temperatura
↓
Arquivos CSV / API / Serial / MQTT
↓
Processamento dos dados
↓
Banco de dados (MySQL/SQLite)
↓
Dashboard PCM_Sistema
↓
Visualização e análise dos resultados
```

## 11. Exemplos de uso

Exemplos práticos do fluxo do projeto:

- carregamento de dados capturados por sensores ou arquivos CSV;
- visualização de gráficos térmicos no dashboard;
- realização de cálculos térmicos e análise de desempenho;
- comparação entre múltiplas fontes de temperatura.

A experiência típica envolve iniciar a aplicação, conectar ou carregar os dados, abrir a interface de dashboard e analisar as métricas geradas.

## 12. Desenvolvimento futuro

Possíveis direções de evolução do projeto incluem:

- expansão para novos tipos de sensores;
- integração com inteligência artificial e análise preditiva;
- melhoria dos dashboards e visualizações;
- otimização do modelo de persistência e do banco;
- deploy em ambiente servidor ou nuvem;
- automação de importação e exportação de dados.

## 13. Contribuição

Contribuições são bem-vindas. Para colaborar com o projeto, recomenda-se:

1. criar um fork do repositório;
2. criar uma branch para a alteração proposta;
3. implementar a mudança com testes ou validação local;
4. abrir um pull request descrevendo o problema e a solução.

## 14. Licença

Nenhuma licença explícita foi identificada no repositório até o momento. Recomenda-se verificar essa informação com o mantenedor antes de utilizar o projeto em contextos comerciais ou distribuídos publicamente.
