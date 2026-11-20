# Preparação e publicação no Apidog

## Arquivos de entrada

- Importe `openapi.json`, que está nesta pasta, em formato OpenAPI/Swagger.
- Crie um documento Markdown chamado **README** na árvore de APIs e cole todo o conteúdo de `README.md` desta pasta. O texto também aparece na descrição geral do contrato, mas isso não substitui o documento separado exigido.

## Importar e organizar

1. Entre na sua conta do Apidog e crie o projeto **Doni Transportes — API de Orçamentos**. Se optar por Spec-first, mantenha o arquivo do contrato como fonte; o modo é escolhido na criação.
2. Na árvore de APIs, use **+ → Import**, ou **Settings → Import Data**. Escolha `openapi.json` e confira o formato OpenAPI.
3. Na prévia, confirme **10 endpoints** e importe todos os schemas/componentes.
4. Confira duas pastas: **Clientes** e **Solicitações de orçamento**, organizadas pelas tags. Caso a importação não forme as pastas, crie-as e mova os 5 endpoints correspondentes para cada uma.
5. Crie **+ → New Markdown**, nome **README**, e cole o documento indicado acima.
6. Abra Schemas/Data Schemas e confirme os modelos Cliente, CreateClienteDTO, UpdateClienteDTO, SolicitacaoOrcamento, CreateSolicitacaoDTO, UpdateSolicitacaoDTO, ApiError e seus auxiliares.
7. Abra POST e PATCH e confirme que os corpos e respostas mantêm referência aos componentes. Não converta para objetos inline.

O servidor local está no contrato como `http://127.0.0.1:3000`. Se usar Import Servers as Environments, ele pode ser criado como ambiente de desenvolvimento. O ambiente público de demonstração deve ser **Cloud Mock**, usando a URL gerada pelo próprio Apidog; não invente ou copie um ID de projeto de exemplo.

## Conferir os mocks antes do backend

1. Selecione o ambiente **Cloud Mock** e abra GET `/api/v1/clientes`.
2. Use a aba Mock e teste a URL disponibilizada pelo Apidog, com o método correto. Deve haver uma resposta 200 com `dados` e `paginacao`.
3. Confira os campos Mock nos schemas. O contrato inclui a extensão oficial `x-apidog-mock`, com regras Faker para UUID, nome, e-mail e instantes. Para campos restritos, usa valores válidos fixos e enums.
4. Se o projeto priorizar exemplos de resposta, as respostas serão fixas. Selecione a geração por schema para observar dados dinâmicos e confira se as regras foram preservadas na importação. Caso não tenham sido, configure-as na coluna Mock do schema usando o seletor do Apidog.
5. Teste o POST de cada entidade (201), a consulta individual (200), PATCH (200) e DELETE (204 sem corpo).
6. Confira também os exemplos 400, 404, 409 e 422. Cada resposta pode ter sua própria URL de Mock. Para alternar automaticamente conforme parâmetros, configure expectativas no Advanced Mock.

O mock gera dados e exemplos: não equivale a um CRUD persistente nem garante validações de negócio. POST seguido de GET pode não retornar o mesmo registro. O mock **não envia e-mail**; statusEmail é apenas simulado. Os exemplos fixos mantêm o mesmo clienteId para facilitar a explicação do relacionamento.

## Roteiro na API real

Após revisar o contrato e simular, execute `npm start`, selecione o ambiente local e siga esta sequência:

| Passo | Requisição | Verificação |
| --- | --- | --- |
| 1 | POST /api/v1/clientes | 201; copie o id; Location aponta ao cliente |
| 2 | GET /api/v1/clientes?pagina=1&limite=10&busca=Exemplo | 200 com paginação |
| 3 | GET /api/v1/clientes/{id} | 200; id do passo 1 |
| 4 | PATCH /api/v1/clientes/{id} | 200; altere nome |
| 5 | POST /api/v1/solicitacoes-orcamento | 201; use clienteId do passo 1 |
| 6 | GET /api/v1/solicitacoes-orcamento?status=RECEBIDA | 200; pedido registrado |
| 7 | GET /api/v1/solicitacoes-orcamento/{id} | 200; consulte statusEmail |
| 8 | PATCH /api/v1/solicitacoes-orcamento/{id} | 200; status EM_ANALISE |
| 9 | DELETE /api/v1/clientes/{id} | 409, pois há pedido vinculado |
| 10 | DELETE /api/v1/solicitacoes-orcamento/{id} | 204 sem corpo |
| 11 | DELETE /api/v1/clientes/{id} | 204 sem corpo |
| 12 | GET de um id já excluído | 404 com ApiError |

Para validar 422, envie e-mail inválido, peso negativo, data inexistente, enum desconhecido ou PATCH vazio. Para 400, envie JSON malformado, UUID inválido ou pagina=0. Para verificar o fluxo comercial, configure o Gmail e envie um pedido com dados de teste autorizados; confira o destinatário, Reply-To e o link do cliente. Os testes automatizados usam transporte simulado e não comprovam entrega real no Gmail.

## Quick Share — entrega no Teams

1. Acesse **Share Docs → Quick Share** e crie o compartilhamento.
2. Inclua README, as duas pastas com todos os endpoints e os schemas.
3. Habilite **Try it out** e disponibilize o ambiente **Cloud Mock** aos leitores. Não publique segredos de ambientes SMTP nem use o ambiente local como única opção.
4. Se definir senha, registre-a junto ao link. O objetivo da atividade é um link público acessível ao avaliador.
5. Abra a URL em uma sessão sem login e verifique README, os 10 endpoints, os schemas e uma chamada pelo Cloud Mock.
6. Envie a URL gerada pelo Apidog no Teams. Este repositório ou o arquivo OpenAPI não substitui o link.

## Critérios e pendências

| Critério | Preparação |
| --- | --- |
| README com contexto, arquitetura e autoria | Texto pronto em docs/README.md; criar documento separado no Apidog |
| 2 entidades e 10 operações CRUD | Contrato pronto |
| Schemas reutilizáveis | 20 componentes; corpos e respostas por referência |
| Metadados, restrições, exemplos e mocks | Incluídos; conferir importação e execução no Cloud Mock |
| URL pública com Try it out | Pendente de publicação na conta do autor |

## Referências oficiais

- [Importar OpenAPI](https://docs.apidog.com/import-openapi-spec-635046m0)
- [Importação manual](https://docs.apidog.com/manual-import-633884m0)
- [Extensão x-apidog-mock](https://docs.apidog.com/x-apidog-mock-1981687m0)
- [Mocks do Apidog](https://docs.apidog.com/mock-api-data-in-apidog-617869m0)
- [Expectativas condicionais](https://docs.apidog.com/en/how-to-mock-conditional-data-in-apidog-748063m0)
- [Quick Share e ambientes de Try it out](https://docs.apidog.com/quick-share-630189m0)
