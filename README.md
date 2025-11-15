# Projeto de Sistema Distribuído com Múltiplos Bancos de Dados

Este projeto implementa uma arquitetura baseada em microserviços que se comunicam entre si e utilizam diferentes tipos de bancos de dados. O objetivo principal é demonstrar integração entre serviços, geração e armazenamento de dados em múltiplos bancos e consulta consolidada a partir de um serviço central.

## 1. Tema escolhido

O tema escolhido foi um sistema de catálogo de filmes com usuários e avaliações. O sistema contém três tipos de informações distintas:<br>
-Filmes<br>
-Usuários<br>
-Avaliações (ratings)<br>

Cada tipo de dado é armazenado em um banco diferente e tratado por um microserviço específico.<br>
O serviço S1 atua como agregador central, recebendo solicitações externas e repassando chamadas para os serviços especializados (S2). Este modelo foi escolhido por permitir utilização clara de múltiplos bancos, separação de responsabilidades e simulação de um ambiente real de microserviços.

## 2. Bancos escolhidos

#### 1. Banco Relacional (RDB): PostgreSQL

Usado para armazenamento de usuários.<br>
Motivos:<br>
-Integridade referencial<br>
-Suporte sólido a transações<br>
-Estrutura tabular adequada para dados consistentes como cadastro de pessoas<br>
-Facilita consultas com ordenação e paginação<br>

#### 2. Banco NoSQL 1: MongoDB

Usado para armazenamento de filmes.<br>
Motivos:<br>
-Estrutura flexível para documentos, adequada para filmes que podem ter campos variados<br>
-Suporte nativo a objetos complexos<br>
-Modelo documental simples de manipular em microserviços<br>

#### 3. Banco NoSQL 2: Redis

Usado para avaliações e para cálculos de agregação (contagem e soma de notas).<br>
Motivos:<br>
-Excelente desempenho para operações de leitura/escrita frequentes<br>
-Adequado para cenários com atualizações rápidas<br>
-Estrutura de chave-valor simples para estatísticas por filme<br>

## 3. Como executar o projeto

#### 3.1 Pré-requisitos

Nenhum software precisa estar instalado previamente, exceto:<br>
-Docker<br>
-Docker Compose<br>

Todo o ambiente sobe automaticamente usando containers. Todos os bancos, serviços e dependências são criados na primeira execução.

#### 3.2 Passos para executar

1) Clonar o repositório<br>

2) Rodar todos os serviços:<br>
OBS: docker compose up -d --build<br>

3) Verificar se os containers estão em execução:<br>
OBS: docker ps<br>

Cada serviço possui suas próprias rotas para criação, busca e exclusão de dados.<br>
O ambiente não exige nenhuma configuração manual de bancos ou instalação local de dependências.

