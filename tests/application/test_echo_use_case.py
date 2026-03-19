from application.echo_use_case import EchoUseCase


class TestEchoUseCase_Execute:
    def test_echo_returns_exact_message(self):
        # Arrange
        use_case = EchoUseCase()
        msg = "Hello World"

        # Act
        result = use_case.execute(message=msg)

        # Assert
        assert result == msg
