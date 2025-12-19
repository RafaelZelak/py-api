# Clean Architecture FastAPI

Este projeto segue uma arquitetura limpa (Clean Architecture) focada em simplicidade, escalabilidade e alta concorrência.

## Estrutura do Projeto

A aplicação é dividida em camadas com responsabilidades bem definidas:

1.  **Transport (`transport/`)**: Camada de entrada (HTTP/FastAPI). Só conhece "pedidos" e "respostas".
2.  **Application (`application/`)**: Casos de uso (Regras da aplicação). Orquestra o fluxo.
3.  **Domain (`domain/`)**: Regras de negócio puras e entidades. O coração do sistema.
4.  **Infrastructure (`infrastructure/`)**: Implementações concretas (Banco de dados, APIs externas).

## Diretrizes de Desenvolvimento

### Quando usar cada camada?

#### 1. Domain (`domain/`) - O Coração

Use quando tiver **Regras de Negócio** que independem de tecnologia.

- **Entidades**: Classes que representam o negócio (ex: `User`, `Product`).
- **Value Objects**: Tipos imutáveis (ex: `Email`, `CPF`).
- **Exceptions**: Erros de negócio (ex: `InsufficientFundsError`).

> **Exemplo**: Calcular se um usuário é maior de idade. Isso é regra de negócio, não depende de banco ou HTTP.

#### 2. Infrastructure (`infrastructure/`) - O "Como"

Use para tudo que envolve **IO (Input/Output)** e ferramentas externas.

- **Repositórios**: Implementação do acesso ao banco (SQLAlchemy, Mongo).
- **Clients**: Chamadas para APIs externas (Stripe, AWS).
- **Cache**: Redis, Memcached.

> **Regra de Ouro**: O `domain` define _o que_ precisa ser salvo (interface), a `infrastructure` define _como_ salvar (SQL).

---

## Diretrizes de Desenvolvimento

Para manter a qualidade e a consistência do código, siga rigorosamente estas diretrizes:

### 1. Código Auto-Explicativo

- **Evite comentários óbvios**. O código deve ser legível por si só.
- Se você precisa explicar _o que_ o código faz, provavelmente precisa refatorar.
- Use comentários apenas para explicar _o porquê_ de decisões complexas ou não intuitivas.

### 2. Nomenclatura Padronizada

Mantenha consistência entre nomes de arquivos, classes e funções.

- **Arquivos e Diretórios**: `snake_case` (ex: `create_user_use_case.py`)
- **Classes**: `PascalCase` (ex: `CreateUserUseCase`)
- **Funções e Variáveis**: `snake_case` (ex: `create_user`, `user_id`)
- **Constantes**: `UPPER_CASE` (ex: `MAX_RETRIES`)

### 3. Responsabilidade Única (Single Responsibility)

- Cada arquivo deve ter **uma única responsabilidade**.
- Cada rota deve ter seu próprio arquivo em `transport/http/v1/routes/`.
- Cada caso de uso deve ter seu próprio arquivo em `application/`.

---

## Como Criar uma Nova Rota

Siga este fluxo para adicionar uma nova funcionalidade (ex: "Criar Usuário").

### Passo 1: Application (Caso de Uso)

Crie o arquivo do caso de uso. O nome do arquivo deve refletir a ação.

**Arquivo:** `application/create_user_use_case.py`

```python
class CreateUserUseCase:
    def execute(self, name: str, email: str) -> dict:
        # Lógica de orquestração aqui
        return {"id": 1, "name": name, "email": email}
```

### Passo 2: Transport (Schemas)

Defina os contratos de entrada e saída.

> **Por que usar Schemas?**
> Para quem vem de um Python mais dinâmico, criar arquivos só para "tipar" pode parecer verboso. Mas em APIs robustas, isso é vital:
>
> 1.  **Contrato de Interface**: Define exatamente o que entra e sai.
> 2.  **Validação Automática**: Garante que os dados estão certos antes de chegarem na lógica.
> 3.  **Documentação Automática**: Gera o Swagger/OpenAPI automaticamente.
> 4.  **Segurança**: Evita vazamento de dados sensíveis no retorno.

**Arquivo:** `transport/http/v1/schemas/create_user.py`

```python
from pydantic import BaseModel

class CreateUserRequest(BaseModel):
    name: str
    email: str

class CreateUserResponse(BaseModel):
    id: int
    name: str
    email: str
```

### Passo 3: Transport (Rota)

Crie a rota isolada. Ela deve apenas converter HTTP para o Caso de Uso e vice-versa.

**Arquivo:** `transport/http/v1/routes/create_user.py`

```python
from fastapi import APIRouter
from transport.http.v1.schemas.create_user import CreateUserRequest, CreateUserResponse
from application.create_user_use_case import CreateUserUseCase

router = APIRouter()

@router.post("/users", response_model=CreateUserResponse)
def create_user(request: CreateUserRequest):
    use_case = CreateUserUseCase()
    result = use_case.execute(request.name, request.email)
    return CreateUserResponse(**result)
```

### Passo 4: Registrar a Rota

Adicione a nova rota no arquivo principal.

**Arquivo:** `main.py`

```python
from transport.http.v1.routes.create_user import router as create_user_router

# ...
app.include_router(create_user_router, prefix="/api/v1")
```

---

## Docker & Deploy

O projeto está totalmente dockerizado e pronto para deploy escalável.

### Como Rodar com Docker Compose

O ambiente inclui a API e um Nginx como Reverse Proxy.

```bash
docker-compose up --build -d
```

A API estará acessível em `http://localhost/api/v1/ping` (Porta 80).

### Guia de Deploy Blue-Green (Zero Downtime)

O **Blue-Green Deployment** é uma técnica para reduzir riscos e tempo de inatividade executando duas versões idênticas de produção chamadas Blue e Green.

Neste projeto, o **Nginx** atua como o "switch" que direciona o tráfego.

#### Passo a Passo para Deploy Manual:

1.  **Estado Inicial (Blue)**:

    - Sua aplicação está rodando no container `py-api-app` (digamos que seja a versão Blue).
    - O Nginx aponta para `http://api:8000`.

2.  **Subir a Nova Versão (Green)**:

    - Você cria uma nova versão da imagem Docker.
    - Sobe um novo container (ex: `py-api-app-v2`) em uma porta diferente ou na mesma rede com outro nome.
    - _Nota: Em um ambiente real orquestrado (K8s, ECS), isso é automático. Com Docker Compose puro, você editaria o `docker-compose.yml` para adicionar o novo serviço ou usaria tags._

3.  **A Alternância (The Switch)**:

    - Edite o arquivo `nginx/nginx.conf`.
    - Altere o bloco `upstream` para apontar para o novo container:
      ```nginx
      upstream api_backend {
          server api-v2:8000; # Aponta para o novo container (Green)
      }
      ```

4.  **Reload do Nginx**:

    - Aplique a mudança sem derrubar conexões:
      ```bash
      docker exec -it py-api-nginx nginx -s reload
      ```
    - Agora todo o tráfego vai para a versão Green.

5.  **Desligar o Blue**:
    - Se tudo estiver ok com a versão Green, você pode parar e remover o container da versão Blue.
