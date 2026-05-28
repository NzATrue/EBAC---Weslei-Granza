# Modulo 31 | Streamlit V | Exercicio 2

**Por:** Weslei Granza  
**Data:** 28 de maio de 2026

## Descricao

Aplicacao em Streamlit para analise da base `online_shoppers_intention.csv`, com exploracao dos dados e agrupamento hierarquico usando distancia de Gower.

O projeto usa a base disponibilizada no exercicio. Para manter o deploy estavel no plano gratuito do Render, o aplicativo permite ajustar a quantidade de registros processados na matriz de distancia.

## Links

- Aplicacao no Render: cole aqui o link apos o deploy
- Repositorio GitHub: https://github.com/NzATrue/EBAC---Weslei-Granza/tree/main/Modulo_31_Streamlit_V/Exercicio_2

## Como executar localmente

```bash
pip install -r requirements.txt
streamlit run mod31_ex2_projeto_AgrupamentoHierarquico.py
```

## Deploy no Render

Ao criar o Web Service no Render, use:

- Root Directory: `Modulo_31_Streamlit_V/Exercicio_2`
- Build Command: `pip install -r requirements.txt`
- Start Command: `streamlit run mod31_ex2_projeto_AgrupamentoHierarquico.py --server.port $PORT --server.address 0.0.0.0`

## Arquivos principais

- `mod31_ex2_projeto_AgrupamentoHierarquico.py`: aplicacao Streamlit
- `online_shoppers_intention.csv`: base de dados usada localmente
- `requirements.txt`: dependencias
- `render.yaml`: configuracao para deploy
