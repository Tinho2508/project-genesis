# Visao Geral do Projeto

## O que e o Project Genesis?

O **Project Genesis** e uma plataforma de IA focada em **geracao de codigo a partir de instrucoes em linguagem natural**. O objetivo e permitir que desenvolvedores descrevam *o que* querem em portugues, e o sistema gere o codigo correspondente.

## Problema que Resolve

Escrever codigo e demorado e requer conhecimento tecnico especifico. O Genesis busca:

- **Acelerar o desenvolvimento** gerando boilerplate e funcoes comuns
- **Aumentar a produtividade** de desenvolvedores
- **Democratizar a programacao** permitindo que nao-programadores criem solucoes simples

## Arquitetura

```
Instrucao em Texto --> Tokenizacao --> Modelo de Linguagem --> Codigo Gerado
                        (HF)           (CodeGPT)              (Python)
```

## Status Atual

| Componente | Status |
|:---|:---|
| Configuracao do modelo | Implementado |
| Pipeline de dados | Implementado |
| Loop de treinamento | Implementado |
| Inference (geracao) | Implementado |
| CLI interativa | Implementado |
| UI grafica | Planejado |
| Avaliacao automatizada | Planejado |

## Tecnologias

- **PyTorch** - Framework de deep learning
- **Hugging Face Transformers** - Modelos de linguagem pre-treinados
- **CodeGPT** - Modelo base para geracao de codigo Python
- **Jupyter Notebooks** - Experimentacao e prototipagem

## Roadmap

- [x] Fase 1: Prototipacao com modelo pre-treinado
- [x] Fase 2: Pipeline de treinamento com dados customizados
- [ ] Fase 3: Fine-tuning com datasets de codigo maiores
- [ ] Fase 4: Interface grafica para interacao
- [ ] Fase 5: Avaliacao automatizada (BLEU, pass@k)
- [ ] Fase 6: Deploy como API
