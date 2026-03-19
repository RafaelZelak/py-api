# Error Handler

Este documento descreve o contrato de erros da API, como ele funciona em cada camada, como usar as exceções existentes e como adicionar novas.

---

## Filosofia

Erros são parte do contrato do sistema, não acidentes. Cada camada fala seu próprio idioma:

- **Domain** → regras de negócio (`ResourceNotFoundError`, `BusinessRuleViolationError`, etc.)
- **Infrastructure** → falhas técnicas capturadas e reembaladas como `InfrastructureError`
- **Application** → apenas propaga. Nunca captura.
- **Transport** → único tradutor para HTTP. Um handler global, zero `try/except` nas rotas.

---

## Formato de Resposta (imutável)

Toda resposta de erro da API segue exatamente este schema, sem exceção:

```json
{
  "error_code": "RESOURCE_NOT_FOUND",
  "message": "Product not found",
  "details": {}
}
```

| Campo        | Tipo     | Descrição                                                    |
|--------------|----------|--------------------------------------------------------------|
| `error_code` | `string` | Identificador semântico do erro, sempre em `SCREAMING_SNAKE` |
| `message`    | `string` | Mensagem legível, segura para exibir ao cliente              |
| `details`    | `object` | Informações extras (ex: campos de validação). Pode ser `{}` |

---

## Hierarquia de Exceções

Todas herdam de `DomainException` definida em `core/exceptions.py`.

```
DomainException
├── ResourceNotFoundError        → RESOURCE_NOT_FOUND        / 404
├── ResourceAlreadyExistsError   → RESOURCE_ALREADY_EXISTS   / 409
├── BusinessRuleViolationError   → BUSINESS_RULE_VIOLATION   / 422
├── ValidationError              → DOMAIN_VALIDATION_ERROR   / 422
├── UnauthorizedError            → UNAUTHORIZED              / 401
├── ForbiddenError               → FORBIDDEN                 / 403
└── InfrastructureError          → INFRASTRUCTURE_ERROR      / 500
```

Além dessas, o handler global cobre dois casos automaticamente:

| Origem | `error_code` | HTTP |
|--------|-------------|------|
| `RequestValidationError` do Pydantic | `REQUEST_VALIDATION_ERROR` | 422 |
| Qualquer `Exception` não mapeada | `INTERNAL_SERVER_ERROR` | 500 |

---

## Responsabilidade por Camada

### Domain (`domain/`)

A camada de domínio **define** e **lança** exceções. Nunca importa FastAPI.

```python
# domain/ports/order_repository.py ou qualquer use case no application/
from core.exceptions import ResourceNotFoundError, BusinessRuleViolationError

# Recurso não existe
raise ResourceNotFoundError("Order not found")

# Regra de negócio violada
raise BusinessRuleViolationError("Cannot cancel a shipped order")

# Validação de domínio (ex: formato inválido de dado de negócio)
from core.exceptions import ValidationError
raise ValidationError("CPF must have 11 digits")

# Com detalhes opcionais
raise ResourceNotFoundError("Product not found", details={"product_id": product_id})
```

**Quando usar cada exceção:**

| Exceção | Usar quando |
|---------|-------------|
| `ResourceNotFoundError` | Recurso buscado por ID/chave não existe |
| `ResourceAlreadyExistsError` | Tentativa de criar algo que já existe (email duplicado, slug, etc.) |
| `BusinessRuleViolationError` | Regra de negócio impede a operação (status inválido, limite excedido) |
| `ValidationError` | Dado semanticamente inválido no domínio (CPF, formato de data, etc.) |
| `UnauthorizedError` | Requisição sem credenciais válidas |
| `ForbiddenError` | Credenciais válidas, mas sem permissão para o recurso |

---

### Infrastructure (`infrastructure/`)

A camada de infra **captura** erros de libs externas (SQLAlchemy, Redis, HTTP clients) e os **reembala** como `InfrastructureError`. Nenhum detalhe interno vaza.

```python
from sqlalchemy.exc import SQLAlchemyError
from core.exceptions import InfrastructureError

def find_by_id(self, user_id: int) -> Optional[User]:
    try:
        # ...query...
    except SQLAlchemyError as database_error:
        raise InfrastructureError("Database operation failed") from database_error
```

O `from database_error` preserva o traceback original nos logs do servidor, sem expô-lo ao cliente.

---

### Application (`application/`)

A camada de aplicação **não captura nada**. Apenas orquestra e propaga.

```python
# CORRETO
class CreateOrderUseCase:
    def execute(self, customer_id: int, items: list) -> Order:
        customer = self.customer_repo.find_by_id(customer_id)  # pode lançar ResourceNotFoundError
        if not items:
            raise BusinessRuleViolationError("Order must have at least one item")
        return self.order_repo.save(Order(customer=customer, items=items))

# ERRADO — nunca faça isso na Application
class CreateOrderUseCase:
    def execute(self, ...):
        try:
            ...
        except ResourceNotFoundError:
            raise HTTPException(status_code=404, ...)  # ❌ importar FastAPI na Application
```

---

### Transport (`transport/`)

As rotas são **call-throughs puros**. Zero `try/except`. A validação dos dados de entrada é responsabilidade do Pydantic — o handler global converte `RequestValidationError` automaticamente.

```python
# CORRETO
@router.post("/orders", response_model=OrderResponse)
def create_order(request: CreateOrderRequest, db: Session = Depends(get_db)):
    repository = SQLAlchemyOrderRepository(db)
    use_case = CreateOrderUseCase(repository)
    return use_case.execute(request.customer_id, request.items)

# ERRADO
@router.post("/orders", response_model=OrderResponse)
def create_order(request: CreateOrderRequest, db: Session = Depends(get_db)):
    try:                                    # ❌ try/except manual na rota
        ...
    except SomeError as e:
        raise HTTPException(...)
```

O handler global está registrado em `transport/http/error_handler.py` e ativado em `main.py` com `register_exception_handlers(app)`.

---

## Como Adicionar um Novo Erro

### Passo 1 — Declarar a exceção em `core/exceptions.py`

```python
# core/exceptions.py

class PaymentDeclinedError(DomainException):
    error_code = "PAYMENT_DECLINED"
    http_status = 402
```

O `http_status` e o `error_code` ficam junto da exceção — o handler lê esses atributos automaticamente. Não é necessário alterar `error_handler.py`.

### Passo 2 — Usar onde necessário

```python
from core.exceptions import PaymentDeclinedError

raise PaymentDeclinedError("Card was declined by the issuer")

# Com detalhes para o cliente
raise PaymentDeclinedError(
    "Card was declined by the issuer",
    details={"reason": "insufficient_funds"}
)
```

### Passo 3 — Testar

Adicione um cenário em `tests/test_error_handler.py` seguindo o padrão existente:

```python
# Em _build_test_app():
@app.get("/raise/payment-declined")
def raise_payment_declined():
    raise PaymentDeclinedError("Card was declined by the issuer")

# Em TestErrorHandler_DomainExceptions:
def test_payment_declined(self, client: TestClient):
    response = client.get("/raise/payment-declined")
    assert response.status_code == 402
    body = response.json()
    _assert_error_schema(body)
    assert body["error_code"] == "PAYMENT_DECLINED"
```

---

## Erros com `details`

O campo `details` é livre e tipado como `dict[str, Any]`. Use para enriquecer o contexto sem vazar internals:

```python
# Validação com campos problemáticos
raise ValidationError(
    "Invalid order data",
    details={"quantity": "must be greater than 0", "sku": "not found in catalog"}
)

# Recurso com contexto
raise ResourceNotFoundError(
    "Product not found",
    details={"product_id": product_id}
)
```

O handler de `RequestValidationError` (Pydantic) popula `details` automaticamente com `{campo: mensagem}` para cada campo que falhou:

```json
{
  "error_code": "REQUEST_VALIDATION_ERROR",
  "message": "Request validation failed",
  "details": {
    "email": "value is not a valid email address",
    "age": "Input should be greater than 0"
  }
}
```

---

## O que o Handler Garante

| Garantia | Como |
|----------|------|
| Nenhuma rota com `try/except` manual | Exceções propagam até o handler global |
| HTTP 500 nunca expõe stack trace | Catch-all retorna mensagem genérica; traceback vai só pro log |
| HTTP 422 de validação sempre popula `details` | Handler do Pydantic extrai `loc` + `msg` por campo |
| Schema de resposta sempre idêntico | `error_code`, `message`, `details` em todo erro |
| Erros de infra não vazam detalhes de lib | `InfrastructureError` encapsula qualquer `SQLAlchemyError`, etc. |
