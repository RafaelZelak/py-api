# Guia de Testes

Este guia define o padrão ouro para a criação de testes automáticos neste projeto. Os testes são **MUITO IMPORTANTES** e devem ser tratados como documentação viva do contrato do sistema.

Todos os testes desenvolvidos no projeto devem obrigatoriamente seguir as diretrizes abaixo.

---

## 1. Organização e Nomenclatura

* **Arquivos:** Devem ser nomeados no formato `test_*.py` (padrão Pytest).
* **Agrupamento:** Agrupe os testes por método público ou comportamento exportado em classes.
* **Nomenclatura da Classe:** `Test<Tipo>_<Metodo>`
* **Nomenclatura do Método de Teste (Cenário):** Curto, descritivo e em minúsculo, focado no comportamento (nunca na implementação técnica). Ex: `test_happy_path`, `test_invalid_format`, `test_stops_on_sentinel_error`.

**Exemplo:**
```python
class TestCreateUserUseCase_Execute:
    def test_happy_path(self):
        ...

    def test_email_already_registered(self):
        ...
```

---

## 2. Estrutura Padrão (AAA)

Todos os testes sem exceção devem seguir **rigorosamente** o padrão **AAA (Arrange, Act, Assert)**. Não misture as fases.

```python
def test_validates_and_saves_user(self):
    # 1. Arrange (Preparação)
    fake_repo = FakeUserRepository()
    use_case = CreateUserUseCase(fake_repo)
    request_data = {"name": "Alice", "email": "alice@test.com"}

    # 2. Act (Ação)
    result = use_case.execute(**request_data)

    # 3. Assert (Verificação)
    assert result.id is not None
    assert result.email == "alice@test.com"
    assert fake_repo.saved_user == result
```

Setup compartilhado entre fases é permitido apenas se melhorar a clareza geral e não obscurecer a intenção do teste.

---

## 3. Política de Mocks e Fakes

**Dê preferência quase absoluta a Fakes manuais** em vez de bibliotecas de Mock (como `unittest.mock` ou `pytest-mock`) para Use Cases, adaptadores e componentes de negócio.

Fakes manuais devem:
* Ser minimalistas.
* Implementar apenas os métodos exigidos pelo contrato (Interface/Port class).
* Expor seu estado interno explicitamente caso haja verificação de chamadas (ex: `self.called = True`, `self.saved_entity = entity`).

Apenas utilize frameworks de Mock se:
* A dependência for muito complexa de ser simulada manualmente.
* For estritamente necessário validar contagem de chamadas ou ordem de argumentos complexos e o Fake Manual poluir muito o teste.

**Exemplo de Fake Manual aceitável:**
```python
class FakeUserRepository(UserRepository):
    def __init__(self):
        self.users = {}
        self.save_called = False

    def find_by_email(self, email: str):
        return self.users.get(email)

    def save(self, user: User):
        self.save_called = True
        user.id = len(self.users) + 1
        self.users[user.email] = user
        return user
```

---

## 4. Minimalismo na Entrada (Input Minimalism)

* Construa apenas os campos ou estruturas essenciais para a regra que está sendo testada.
* Evite "ruído" nos dados de entrada preenchendo 20 campos de um objeto quando apenas 1 define o fluxo daquele teste.

```python
# Correto (Focado no contrato testado)
minimal_user = User(email="test@test.com", is_active=True)

# Errado (Ruído desnecessário)
noisy_user = User(id=999, name="Test", email="test@test.com", password_hash="xyz", is_active=True, created_at="2024...", updated_at="2024...")
```

---

## 5. Assertions e Tratamento de Erros

* Faça descrições explícitas de seus Asserts para falhas compreensíveis.
* Quando testar **erros de fluxo/sentinel** ou regras de negócio que lançam exceções, utilize **sempre** a interceptação explícita do Pytest validando o tipo da exceção.

```python
import pytest
from core.exceptions import ResourceAlreadyExistsError

def test_raises_error_when_email_exists(self):
    # Arrange
    fake_repo = FakeUserRepository(existing_email="test@test.com")
    use_case = CreateUserUseCase(fake_repo)

    # Act & Assert
    with pytest.raises(ResourceAlreadyExistsError) as exc_info:
        use_case.execute(name="Bob", email="test@test.com", password="123")
    
    # Assert
    assert exc_info.value.error_code == "RESOURCE_ALREADY_EXISTS"
```

---

## 6. Cobertura Exigida (Contract-Driven Testing)

Para todo comportamento exportado do sistema, os testes devem cobrir obrigatoriamente:

1. **Happy Path:** O caminho feliz, entradas válidas produzindo a saída esperada perfeitamente.
2. **Edge Cases (Casos Limite):** Valores limiares, structs preenchidas apenas com campos obrigatórios absolutos.
3. **Casos Base:** Inputs vazios, comportamentos padrão absolutos.
4. **Error Handling & Sentinel Errors:** Falhas de dependência simuladas garantindo que o programa toma a decisão correta (seja contornar o erro ou lançar uma DomainException de negócio específica).
5. **Comportamento de Interações:** Garantir que o Use Case delegou responsabilidade corretamente, não chamou dependências caso ocorresse falho de curto-circuito antes (Early Stop).

Atenção: Valide o **comportamento observável** (O QUÊ o método entrega e seus efeitos colaterais contratuais), e evite validar a implementação interna cirurgicamente estruturada (COMO ele fez).

---

## 7. Determinismo Absoluto

Testes devem ser determinísticos e ultra rápidos. Regras inquebráveis:
* **Zero requests reais de rede** para o mundo exterior.
* **Zero conexões reais a bancos de dados** nas camadas de negócio ou em testes unitários.
* **Zero dependência de tempo de máquina/relógio** (se precisar testar tempo, use Data/Hora injetada por Interface/Fake, ou lib como `freezegun`).
* **Zero \`time.sleep()\`**.
* Todos os testes devem ser executados com sucesso em ambiente paralelo.

Qualquer violação deste determinismo reprova o teste imediatamente no CI.
