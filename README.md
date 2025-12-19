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

## Guia Completo: Criando uma Nova Feature

Para garantir que o código continue limpo e escalável, siga este fluxo rigorosamente. Vamos usar como exemplo a criação de um **Produto**.

### Passo 1: Domain (O "O Que")

Comece pelo coração. Defina a **Entidade** (dados) e a **Interface do Repositório** (contrato).
Aqui não entra banco de dados, nem frameworks, apenas Python puro.

**1.1 Entidade** (`domain/product.py`)

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class Product:
    id: Optional[int]
    name: str
    price: float
```

**1.2 Interface do Repositório** (`domain/ports/product_repository.py`)

```python
from abc import ABC, abstractmethod
from domain.product import Product

class ProductRepository(ABC):
    @abstractmethod
    def save(self, product: Product) -> Product:
        pass
```

---

### Passo 2: Infrastructure (O "Como")

Agora implemente a persistência real (Banco de Dados).

**2.1 Modelo ORM** (`infrastructure/models/product.py`)
Define como a tabela é no banco.

```python
from sqlalchemy import Column, Integer, String, Float
from infrastructure.database import Base

class ProductModel(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    price = Column(Float)
```

**2.2 Implementação do Repositório** (`infrastructure/repositories/product_repository.py`)
Implementa a interface do Domain usando o SQLAlchemy.

```python
from sqlalchemy.orm import Session
from domain.product import Product
from domain.ports.product_repository import ProductRepository
from infrastructure.models.product import ProductModel

class SQLAlchemyProductRepository(ProductRepository):
    def __init__(self, db: Session):
        self.db = db

    def save(self, product: Product) -> Product:
        # Converte Domain -> Model
        model = ProductModel(name=product.name, price=product.price)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        # Retorna Model -> Domain
        return Product(id=model.id, name=model.name, price=model.price)
```

---

### Passo 3: Application (A Lógica)

Crie o Caso de Uso. Ele orquestra a operação. Note que ele pede um `ProductRepository` (a interface), não a implementação concreta. Isso é **Inversão de Dependência**.

**Arquivo:** `application/create_product_use_case.py`

```python
from domain.product import Product
from domain.ports.product_repository import ProductRepository

class CreateProductUseCase:
    def __init__(self, repository: ProductRepository):
        self.repository = repository

    def execute(self, name: str, price: float) -> Product:
        # Aqui entrariam validações de negócio (ex: preço não pode ser negativo)
        if price < 0:
            raise ValueError("Price cannot be negative")

        product = Product(id=None, name=name, price=price)
        return self.repository.save(product)
```

---

### Passo 4: Transport (A API)

Agora expomos isso para o mundo via HTTP.

**4.1 Schemas (Contratos)** (`transport/http/v1/schemas/product.py`)
Define o JSON de entrada e saída. Garante validação automática.

```python
from pydantic import BaseModel

class CreateProductRequest(BaseModel):
    name: str
    price: float

class ProductResponse(BaseModel):
    id: int
    name: str
    price: float
```

**4.2 Rota** (`transport/http/v1/routes/products.py`)
Conecta tudo: Recebe o Request -> Instancia o Repo -> Chama o UseCase -> Retorna o Response.

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from infrastructure.database import get_db
from infrastructure.repositories.product_repository import SQLAlchemyProductRepository
from application.create_product_use_case import CreateProductUseCase
from transport.http.v1.schemas.product import CreateProductRequest, ProductResponse

router = APIRouter()

@router.post("/products", response_model=ProductResponse)
def create_product(request: CreateProductRequest, db: Session = Depends(get_db)):
    # 1. Prepara as dependências
    repo = SQLAlchemyProductRepository(db)
    use_case = CreateProductUseCase(repo)

    # 2. Executa a lógica
    try:
        product = use_case.execute(request.name, request.price)
        return product
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

---

### Passo 5: Registrar (O Fim)

Avise o FastAPI que essa rota existe.

**Arquivo:** `main.py`

```python
from transport.http.v1.routes.products import router as products_router

app.include_router(products_router, prefix="/api/v1")
```

---

## Database & Migrations

O projeto utiliza **SQLAlchemy** (ORM) e **Alembic** (Migrações) para gerenciar o banco de dados PostgreSQL.

### O Fluxo de Migração

Toda vez que você alterar um modelo (arquivo em `infrastructure/models/`), você deve criar uma migration para atualizar o banco.

#### 1. Alterar o Modelo

Edite ou crie um modelo em `infrastructure/models/`.
Exemplo: Adicionar uma coluna `age` em `user.py`.

```python
age = Column(Integer, nullable=True)
```

#### 2. Gerar a Migration (Autogenerate)

O Alembic compara seu código Python com o Banco de Dados atual e cria o script de mudança automaticamente.

```bash
docker-compose exec api alembic revision --autogenerate -m "descricao_da_mudanca"
```

> **Importante**: O arquivo será criado em `alembic/versions/` com um timestamp no nome (ex: `20251219_1630_add_age.py`).

#### 3. Aplicar a Migration (Upgrade)

Para efetivar a mudança no banco de dados:

```bash
docker-compose exec api alembic upgrade head
```

#### Comandos Úteis

- **Verificar Status**: Mostra qual a versão atual do banco.

  ```bash
  docker-compose exec api alembic current
  ```

- **Desfazer Última Migration (Downgrade)**:
  ```bash
  docker-compose exec api alembic downgrade -1
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
