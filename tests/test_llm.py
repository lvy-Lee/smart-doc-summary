import pytest
from consts import PROVIDERS


class TestCallLLM:
    def test_basic_call(self, mocker):
        mock_client = mocker.MagicMock()
        mock_resp = mocker.MagicMock()
        mock_resp.choices[0].message.content = "这是摘要"
        mock_client.chat.completions.create.return_value = mock_resp

        from utils import call_llm
        result = call_llm(
            mock_client,
            "测试文本",
            "system prompt",
            "glm-4.7-flash",
            PROVIDERS["智谱AI"],
        )
        assert result == "这是摘要"
        call_kwargs = mock_client.chat.completions.create.call_args[1]
        assert call_kwargs["model"] == "glm-4.7-flash"
        assert call_kwargs["max_tokens"] == 4096
        assert call_kwargs["temperature"] == 0.6
        assert 30 <= call_kwargs["timeout"] <= 300

    def test_thinking_mode(self, mocker):
        mock_client = mocker.MagicMock()
        mock_resp = mocker.MagicMock()
        mock_resp.choices[0].message.content = "思考后摘要"
        mock_client.chat.completions.create.return_value = mock_resp

        from utils import call_llm
        result = call_llm(
            mock_client,
            "测试文本",
            "system prompt",
            "deepseek-reasoner",
            PROVIDERS["DeepSeek"],
        )
        assert result == "思考后摘要"
        call_kwargs = mock_client.chat.completions.create.call_args[1]
        assert call_kwargs["extra_body"] == {"thinking": {"type": "enabled"}}

    def test_no_thinking_for_unsupported(self, mocker):
        mock_client = mocker.MagicMock()
        mock_resp = mocker.MagicMock()
        mock_resp.choices[0].message.content = "普通摘要"
        mock_client.chat.completions.create.return_value = mock_resp

        from utils import call_llm
        result = call_llm(
            mock_client,
            "测试文本",
            "system prompt",
            "qwen-plus",
            PROVIDERS["阿里千问"],
        )
        assert result == "普通摘要"
        call_kwargs = mock_client.chat.completions.create.call_args[1]
        assert "extra_body" not in call_kwargs

    def test_retry_on_failure_then_success(self, mocker):
        mock_client = mocker.MagicMock()
        mock_client.chat.completions.create.side_effect = [
            Exception("第一次失败"),
            mocker.MagicMock(choices=[mocker.MagicMock(message=mocker.MagicMock(content="第二次成功"))]),
        ]

        from utils import call_llm
        result = call_llm(
            mock_client,
            "测试文本",
            "system prompt",
            "glm-4.7-flash",
            PROVIDERS["智谱AI"],
        )
        assert result == "第二次成功"
        assert mock_client.chat.completions.create.call_count == 2

    def test_raises_after_two_failures(self, mocker):
        mock_client = mocker.MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("always fail")

        from utils import call_llm
        with pytest.raises(Exception, match="always fail"):
            call_llm(
                mock_client,
                "测试文本",
                "system prompt",
                "glm-4.7-flash",
                PROVIDERS["智谱AI"],
            )
        assert mock_client.chat.completions.create.call_count == 2

    def test_stream_basic(self, mocker):
        chunks = [
            mocker.MagicMock(choices=[mocker.MagicMock(delta=mocker.MagicMock(content="Hello "))]),
            mocker.MagicMock(choices=[mocker.MagicMock(delta=mocker.MagicMock(content="World"))]),
            mocker.MagicMock(choices=[mocker.MagicMock(delta=mocker.MagicMock(content=None))]),
        ]
        mock_client = mocker.MagicMock()
        mock_client.chat.completions.create.return_value = chunks

        from utils import call_llm_stream
        result = list(call_llm_stream(mock_client, "test", "prompt", "glm-4.7-flash", PROVIDERS["智谱AI"]))
        assert result == ["Hello ", "World"]

    def test_stream_thinking_mode(self, mocker):
        chunks = [
            mocker.MagicMock(choices=[mocker.MagicMock(delta=mocker.MagicMock(content="answer"))]),
        ]
        mock_client = mocker.MagicMock()
        mock_client.chat.completions.create.return_value = chunks

        from utils import call_llm_stream
        result = list(call_llm_stream(mock_client, "test", "prompt", "deepseek-reasoner", PROVIDERS["DeepSeek"]))
        assert result == ["answer"]
        call_kwargs = mock_client.chat.completions.create.call_args[1]
        assert call_kwargs["extra_body"] == {"thinking": {"type": "enabled"}}

    def test_stream_no_thinking_for_unsupported(self, mocker):
        chunks = [
            mocker.MagicMock(choices=[mocker.MagicMock(delta=mocker.MagicMock(content="ok"))]),
        ]
        mock_client = mocker.MagicMock()
        mock_client.chat.completions.create.return_value = chunks

        from utils import call_llm_stream
        result = list(call_llm_stream(mock_client, "test", "prompt", "qwen-plus", PROVIDERS["阿里千问"]))
        assert result == ["ok"]
        call_kwargs = mock_client.chat.completions.create.call_args[1]
        assert "extra_body" not in call_kwargs

    def test_dynamic_timeout(self, mocker):
        mock_client = mocker.MagicMock()
        mock_client.chat.completions.create.return_value = mocker.MagicMock(
            choices=[mocker.MagicMock(message=mocker.MagicMock(content="ok"))]
        )

        from utils import call_llm
        long_text = "a" * 200000
        call_llm(mock_client, long_text, "system prompt", "glm-4.7-flash", PROVIDERS["智谱AI"])
        call_kwargs = mock_client.chat.completions.create.call_args[1]
        expected_timeout = max(30, len(long_text) // 2000 + 30)
        assert call_kwargs["timeout"] == expected_timeout
