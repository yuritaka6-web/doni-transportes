# Doni Transportes — API de Solicitações de Orçamento

## Nome e propósito
API REST para complementar o site da Doni Transportes com cadastro de contatos e solicitações de cotação de frete. Atende pessoas e empresas que precisam transportar cargas e a equipe comercial que analisa os pedidos. O cliente preenche o site e a empresa recebe os dados por e-mail, com Reply-To para o cliente e link para iniciar contato com o WhatsApp dele.

## Arquitetura de recursos
- Cliente: nome, e-mail, WhatsApp e tipo de pessoa.
- Solicitação de orçamento: clienteId, origem, destino, descrição e peso da carga, data desejada, observações, status e estado da notificação.
- Relação 1:N: um cliente pode ter várias solicitações; cada solicitação pertence a exatamente um cliente.
- Localidade, paginação e erro são componentes reutilizáveis, não entidades independentes.
- Uma fila técnica de e-mail acompanha a criação do pedido. O pedido e a fila são persistidos atomicamente; falhas SMTP não apagam o pedido.

## Autoria
| Nome completo | RA | E-mail institucional |
| --- | --- | --- |
| Yuri Vinicius Decaris Trevelin | 2840482321012 | yuri.trevelin@aluno.cps.gov.br |

Trabalho individual por decisão do autor. O enunciado exige grupos de 2 a 4 integrantes; esta composição não atende esse requisito e está sujeita à avaliação do professor.

## Convenções do contrato
- Base: `/api/v1`; JSON UTF-8. Os 10 endpoints estão organizados por tags/pastas.
- UUIDs nos identificadores; datas `YYYY-MM-DD`; instantes RFC 3339 em UTC; pesos em kg.
- POST: 201 com Location; GET/PATCH: 200; DELETE: 204 sem corpo.
- 400: JSON, UUID ou query inválidos; 404: recurso inexistente; 409: cliente com dependências; 422: corpo inválido ou clienteId inexistente; 413: corpo acima de 64 KiB; 415: mídia incorreta; 500: falha interna.
- PATCH exige pelo menos um campo. Omitir mantém o valor. Somente observacoes aceita null, para limpar o conteúdo. Localidades são substituídas integralmente.
- Campos desconhecidos são rejeitados. Na criação, tipoPessoa assume PF, status assume RECEBIDA e observacoes assume null.
- Listas: pagina=1 e limite=20 por padrão; limite máximo 100. Ordenação por criadoEm DESC, id ASC. Clientes aceitam busca; solicitações aceitam status e clienteId. Query desconhecida ou repetida gera 400.
- Não existe restrição de unicidade do e-mail. Cada cadastro representa um contato independente.
- Todos os corpos e respostas JSON referenciam componentes; os objetos de domínio não são definidos inline nas rotas.

## Fluxo e notificações
1. POST /api/v1/clientes cria o contato.
2. POST /api/v1/solicitacoes-orcamento cria o pedido vinculado e uma notificação.
3. A empresa recebe um e-mail com os dados do pedido, contato e link `https://wa.me/55...` do cliente. O destinatário é definido no servidor, nunca pelo navegador.
4. O time consulta e altera o status: RECEBIDA, EM_ANALISE, COTADA ou CANCELADA.

201 confirma o registro. statusEmail=PENDENTE significa que a notificação está na fila; ENVIADO significa aceitação pelo SMTP, sem garantia de entrega na caixa de entrada; FALHOU indica falha com novas tentativas. Sem configuração SMTP o pedido permanece salvo e a notificação permanece pendente. PATCH não reenvia e-mail. A notificação usa uma cópia dos dados no momento da criação. O reenvio segue semântica pelo menos uma vez: uma interrupção após aceitação SMTP pode ocasionar duplicação.

## Design-First e mocks
O arquivo openapi.json é a fonte do contrato; os schemas de entrada são usados pelo backend na validação. Antes de executar o backend, importe o contrato no Apidog e experimente o Cloud Mock.

Há exemplos coerentes de requisição e resposta, incluindo erros e listas, e regras x-apidog-mock nos atributos dinâmicos. Campos de domínio fechado usam enum; telefone e UF usam valores válidos fixos. Configure a geração por schema no Apidog para observar valores dinâmicos. Exemplos fixos mantêm os vínculos entre clienteId e id. O mock não representa banco persistente: POST seguido de GET não comprova persistência, envio real de e-mail nem regras de negócio.

## Limites desta versão
Protótipo acadêmico local, sem autenticação e autorizado a escutar apenas em loopback. A exposição pública dos CRUDs e dos contatos requer autenticação, autorização e proteção contra abuso antes da implantação. O site estático no GitHub Pages não executa este backend Node.js. Não há pagamento, cálculo automático de frete ou rastreamento GPS.
