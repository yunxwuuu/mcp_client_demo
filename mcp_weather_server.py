import json
import httpx
import os
import sys
import logging
from typing import Any
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# 配置日志输出到 stderr，这样不会被 stdio 通信管道捕获
logging.basicConfig(
    level=logging.INFO,
    format='[Server] %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

mcp_server = FastMCP("WeatherServer")
load_dotenv()

WEATHER_API_BASE = "https://api.openweathermap.org/data/2.5/weather"
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
USER_AGENT = "weather-app/1.0"

async def fetch_weather(city: str) -> dict[str, Any] | None:
    """
    从 OpenWeather API 获取天气信息。
    :param city: 城市名称（需使用英文，如 Beijing）
    :return: 天气数据字典；若出错返回包含 error 信息的字典
    """
    if not WEATHER_API_KEY:
        logger.error("❌ WEATHER_API_KEY 未设置")
        return {"error": "WEATHER_API_KEY 未设置"}

    logger.info(f"🌐 正在请求 OpenWeather API key: {WEATHER_API_KEY}")

    params = {
        "q": city,
        "appid": WEATHER_API_KEY,
        "units": "metric",
        "lang": "zh_cn"
    }

    logger.info(f"🌐 正在请求 OpenWeather params: {params}")

    headers = {
        "User-Agent": USER_AGENT
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(WEATHER_API_BASE, params=params, headers=headers)
            response.raise_for_status()
            logger.info(f"✅ API 请求成功: {response.status_code}")
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ HTTP 错误: {e.response.status_code}")
            return {"error": f"HTTP 错误: {e.response.status_code}"}
        except Exception as e:
            logger.error(f"❌ 请求失败: {str(e)}")
            return {"error": f"请求失败: {str(e)}"}

def format_weather(data: dict[str, Any] | str) -> str:
    # 如果传入的是字符串，则先转换为字典
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except Exception as e:
            return f"无法解析天气数据: {e}"

    # 如果数据中包含错误信息，直接返回错误提示
    if "error" in data:
        return f"⚠️ {data['error']}"

    # 提取数据时做容错处理
    city = data.get("name", "未知")
    country = data.get("sys", {}).get("country", "未知")
    temp = data.get("main", {}).get("temp", "N/A")
    humidity = data.get("main", {}).get("humidity", "N/A")
    wind_speed = data.get("wind", {}).get("speed", "N/A")
    # weather 可能为空列表，因此用 [0] 前先提供默认字典
    weather_list = data.get("weather", [{}])
    description = weather_list[0].get("description", "未知")

    return (
        f"🌍 {city}, {country}\n"
        f"🌡  温度: {temp}°C\n"
        f"💧 湿度: {humidity}%\n"
        f"🌬  风速: {wind_speed} m/s\n"
        f"🌤  天气: {description}\n"
    )

@mcp_server.tool()
async def query_weather(city: str) -> str:
    """
    输入指定城市的英文名称，返回今日天气查询结果。
    :param city: 城市名称（需使用英文）
    :return: 格式化后的天气信息
    """
    logger.info(f"🔍 收到天气查询请求: city={city}")
    data = await fetch_weather(city)
    result = format_weather(data)
    logger.info(f"✅ 查询完成，返回结果")
    return result

if __name__ == "__main__":
    # 以标准 I/O 方式运行 MCP 服务器
    mcp_server.run(transport='stdio')