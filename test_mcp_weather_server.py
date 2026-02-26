import pytest
import httpx
import pytest_asyncio
from unittest.mock import patch, AsyncMock, MagicMock
import json

# 导入被测试的模块
from mcp_weather_server import fetch_weather, format_weather, query_weather


class TestFetchWeather:
    """测试 fetch_weather 函数"""

    @pytest.mark.asyncio
    async def test_fetch_weather_success(self):
        """测试成功获取天气数据"""
        mock_response = {
            "name": "Beijing",
            "sys": {"country": "CN"},
            "main": {"temp": 25.5, "humidity": 60},
            "wind": {"speed": 3.5},
            "weather": [{"description": "晴"}]
        }

        with patch('httpx.AsyncClient') as mock_client:
            mock_get = AsyncMock()
            mock_get.get.return_value = MagicMock(
                json=lambda: mock_response,
                raise_for_status=lambda: None
            )
            mock_client.return_value.__aenter__.return_value = mock_get

            result = await fetch_weather("Beijing")

            assert result == mock_response
            mock_get.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_weather_http_error(self):
        """测试 HTTP 错误"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_get = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 404
            http_error = httpx.HTTPStatusError(
                "Not Found",
                request=MagicMock(),
                response=mock_response
            )
            mock_get.get.side_effect = http_error
            mock_client.return_value.__aenter__.return_value = mock_get

            result = await fetch_weather("InvalidCity")

            assert "error" in result
            assert "404" in result["error"]

    @pytest.mark.asyncio
    async def test_fetch_weather_network_error(self):
        """测试网络错误"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_get = AsyncMock()
            mock_get.get.side_effect = Exception("Network error")
            mock_client.return_value.__aenter__.return_value = mock_get

            result = await fetch_weather("Beijing")

            assert "error" in result
            assert "请求失败" in result["error"]


class TestFormatWeather:
    """测试 format_weather 函数"""

    def test_format_weather_success(self):
        """测试格式化天气��据"""
        data = {
            "name": "Beijing",
            "sys": {"country": "CN"},
            "main": {"temp": 25.5, "humidity": 60},
            "wind": {"speed": 3.5},
            "weather": [{"description": "晴"}]
        }

        result = format_weather(data)

        assert "Beijing" in result
        assert "CN" in result
        assert "25.5" in result
        assert "60%" in result
        assert "3.5" in result
        assert "晴" in result

    def test_format_weather_with_error(self):
        """测试包含错误的天气数据"""
        data = {"error": "HTTP 错误: 401"}

        result = format_weather(data)

        assert "⚠️" in result
        assert "HTTP 错误: 401" in result

    def test_format_weather_string_input(self):
        """测试字符串输入"""
        data_str = json.dumps({
            "name": "Shanghai",
            "sys": {"country": "CN"},
            "main": {"temp": 30, "humidity": 70},
            "wind": {"speed": 5},
            "weather": [{"description": "多云"}]
        })

        result = format_weather(data_str)

        assert "Shanghai" in result
        assert "30" in result

    def test_format_weather_invalid_string(self):
        """测试无效字符串"""
        result = format_weather("invalid json")

        assert "无法解析天气数据" in result

    def test_format_weather_missing_fields(self):
        """测试缺失字段"""
        data = {}

        result = format_weather(data)

        assert "未知" in result

    def test_format_weather_empty_weather_list(self):
        """测试空天气列表"""
        data = {
            "name": "Tokyo",
            "sys": {"country": "JP"},
            "main": {"temp": 20, "humidity": 50},
            "wind": {"speed": 2},
            "weather": []
        }

        result = format_weather(data)

        assert "Tokyo" in result


class TestQueryWeatherTool:
    """测试 query_weather 工具"""

    @pytest.mark.asyncio
    async def test_query_weather_success(self):
        """测试查询天气工具成功"""
        mock_data = {
            "name": "Beijing",
            "sys": {"country": "CN"},
            "main": {"temp": 25, "humidity": 60},
            "wind": {"speed": 3},
            "weather": [{"description": "晴"}]
        }

        with patch('mcp_weather_server.fetch_weather', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_data

            result = await query_weather("Beijing")

            assert "Beijing" in result
            assert "CN" in result
            mock_fetch.assert_called_once_with("Beijing")

    @pytest.mark.asyncio
    async def test_query_weather_error(self):
        """测试查询天气工具错误"""
        with patch('mcp_weather_server.fetch_weather', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = {"error": "请求失败"}

            result = await query_weather("InvalidCity")

            assert "⚠️" in result


# 运行测试的入口
if __name__ == "__main__":
    pytest.main([__file__, "-v"])