from application.ping_use_case import PingUseCase


class TestPingUseCase_Execute:
    def test_returns_its_a_live_string(self):
        # Arrange
        use_case = PingUseCase()

        # Act
        result = use_case.execute()

        # Assert
        assert result == "It's a live"
