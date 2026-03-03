import pytest
from unittest.mock import MagicMock, patch

from src.pipeline.graph import RetryInterceptor, BackoffStrategy, JitterStrategy
from stageflow.pipeline.interceptors import ErrorAction


class MockPipelineContext:
    def __init__(self):
        self.data = {}
        self.pipeline_run_id = "test-run-id"
        self.request_id = "test-request-id"


@pytest.fixture
def ctx():
    return MockPipelineContext()


@pytest.fixture
def interceptor():
    return RetryInterceptor(
        max_attempts=3,
        base_delay_ms=100,
        max_delay_ms=1000,
        backoff_strategy=BackoffStrategy.EXPONENTIAL,
        jitter_strategy=JitterStrategy.NONE,
    )


class TestRetryInterceptor:
    @pytest.mark.asyncio
    async def test_before_initializes_retry_state(self, ctx, interceptor):
        await interceptor.before("test_stage", ctx)
        assert ctx.data["_retry.attempt"] == 0
        assert ctx.data["_retry.stage"] == "test_stage"

    @pytest.mark.asyncio
    async def test_before_preserves_existing_retry_state(self, ctx, interceptor):
        ctx.data["_retry.attempt"] = 1
        await interceptor.before("test_stage", ctx)
        assert ctx.data["_retry.attempt"] == 1

    @pytest.mark.asyncio
    async def test_after_clears_retry_state_on_success(self, ctx, interceptor):
        ctx.data["_retry.attempt"] = 2
        ctx.data["_retry.stage"] = "test_stage"
        result = MagicMock()
        result.status = "completed"

        await interceptor.after("test_stage", result, ctx)

        assert "_retry.attempt" not in ctx.data
        assert "_retry.stage" not in ctx.data

    @pytest.mark.asyncio
    async def test_after_preserves_retry_state_on_failure(self, ctx, interceptor):
        ctx.data["_retry.attempt"] = 1
        result = MagicMock()
        result.status = "failed"

        await interceptor.after("test_stage", result, ctx)

        assert ctx.data["_retry.attempt"] == 1

    @pytest.mark.asyncio
    async def test_on_error_returns_fail_for_non_retryable_error(
        self, ctx, interceptor
    ):
        error = ValueError("Invalid input")

        result = await interceptor.on_error("test_stage", error, ctx)

        assert result == ErrorAction.FAIL

    @pytest.mark.asyncio
    async def test_on_error_returns_fail_when_retries_exhausted(self, ctx, interceptor):
        ctx.data["_retry.attempt"] = 2  # Already at max_attempts - 1
        error = ConnectionError("Connection failed")

        result = await interceptor.on_error("test_stage", error, ctx)

        assert result == ErrorAction.FAIL

    @pytest.mark.asyncio
    async def test_on_error_returns_retry_and_increments_attempt(
        self, ctx, interceptor
    ):
        ctx.data["_retry.attempt"] = 0
        error = ConnectionError("Connection failed")

        with patch.object(interceptor, "_calculate_delay", return_value=10):
            result = await interceptor.on_error("test_stage", error, ctx)

        assert result == ErrorAction.RETRY
        assert ctx.data["_retry.attempt"] == 1


class TestBackoffStrategies:
    def test_exponential_backoff(self):
        interceptor = RetryInterceptor(
            base_delay_ms=1000,
            backoff_strategy=BackoffStrategy.EXPONENTIAL,
            jitter_strategy=JitterStrategy.NONE,
        )

        delays = [interceptor._calculate_delay("test", i) for i in range(5)]

        assert delays == [1000, 2000, 4000, 8000, 16000]

    def test_linear_backoff(self):
        interceptor = RetryInterceptor(
            base_delay_ms=1000,
            backoff_strategy=BackoffStrategy.LINEAR,
            jitter_strategy=JitterStrategy.NONE,
        )

        delays = [interceptor._calculate_delay("test", i) for i in range(5)]

        assert delays == [1000, 2000, 3000, 4000, 5000]

    def test_constant_backoff(self):
        interceptor = RetryInterceptor(
            base_delay_ms=1000,
            backoff_strategy=BackoffStrategy.CONSTANT,
            jitter_strategy=JitterStrategy.NONE,
        )

        delays = [interceptor._calculate_delay("test", i) for i in range(5)]

        assert delays == [1000, 1000, 1000, 1000, 1000]

    def test_max_delay_cap(self):
        interceptor = RetryInterceptor(
            base_delay_ms=1000,
            max_delay_ms=5000,
            backoff_strategy=BackoffStrategy.EXPONENTIAL,
            jitter_strategy=JitterStrategy.NONE,
        )

        delay = interceptor._calculate_delay("test", 10)  # Would be 1024000 without cap

        assert delay == 5000


class TestJitterStrategies:
    def test_no_jitter_is_deterministic(self):
        interceptor = RetryInterceptor(
            base_delay_ms=1000,
            jitter_strategy=JitterStrategy.NONE,
        )

        delays = [interceptor._calculate_delay("test", i) for i in range(3)]

        assert delays == [1000, 2000, 4000]

    def test_full_jitter_randomness(self):
        interceptor = RetryInterceptor(
            base_delay_ms=1000,
            jitter_strategy=JitterStrategy.FULL,
        )

        delays = set()
        for _ in range(50):
            delay = interceptor._calculate_delay("test_jitter", 2)
            delays.add(delay)

        assert len(delays) > 1

    def test_equal_jitter_bounds(self):
        interceptor = RetryInterceptor(
            base_delay_ms=1000,
            jitter_strategy=JitterStrategy.EQUAL,
        )

        for _ in range(50):
            delay = interceptor._calculate_delay("test", 2)
            assert 2000 <= delay <= 4000

    def test_decorrelated_jitter(self):
        interceptor = RetryInterceptor(
            base_delay_ms=100,
            max_delay_ms=5000,
            jitter_strategy=JitterStrategy.DECORRELATED,
        )

        delays = [interceptor._calculate_delay("test", i) for i in range(5)]

        for delay in delays:
            assert 100 <= delay <= 5000
