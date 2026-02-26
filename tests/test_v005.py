"""V0.0.5 单元测试"""
import os
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# 添加 src 到路径
src_path = str(Path(__file__).parent.parent / "src")
sys.path.insert(0, src_path)

# 切换到 src 目录以确保模块导入正常
os.chdir(src_path)


class TestConfig:
    """配置模块测试"""

    def test_config_paths(self):
        """测试配置路径"""
        from config import config, DATA_DIR, CONFIG_DIR, LOG_DIR
        assert config.path.data_dir.exists()
        assert DATA_DIR.name == "data"
        assert CONFIG_DIR.name == "config"
        assert LOG_DIR.name == "logs"

    def test_config_from_env(self):
        """测试环境变量配置"""
        os.environ["MAX_CONTEXT_TOKENS"] = "16000"
        from config import Config
        cfg = Config.from_env()
        assert cfg.max_context_tokens == 16000
        os.environ.pop("MAX_CONTEXT_TOKENS", None)


class TestUtils:
    """工具模块测试"""

    def test_get_user_config(self):
        """测试获取用户配置"""
        from utils import get_user_config
        # 不存在的用户返回空字典
        config = get_user_config("nonexistent_user_12345")
        assert isinstance(config, dict)

    def test_save_and_get_user_config(self):
        """测试保存和获取用户配置"""
        from utils import get_user_config, save_user_config
        test_user = "test_user_v005"

        # 保存配置
        test_config = {
            "api_key": "test_key_123",
            "provider": "openai",
            "model": "gpt-3.5-turbo"
        }
        save_user_config(test_user, test_config)

        # 读取配置
        loaded = get_user_config(test_user)
        assert loaded["provider"] == "openai"
        assert loaded["model"] == "gpt-3.5-turbo"
        # api_key 应该被加密
        assert loaded["api_key"].startswith("ENC:")

    def test_encrypt_decrypt(self):
        """测试加密解密"""
        from utils import encrypt_api_key, decrypt_api_key

        original = "sk-test123456"
        encrypted = encrypt_api_key(original)
        assert encrypted != original
        assert encrypted.startswith("ENC:")

        decrypted = decrypt_api_key(encrypted)
        assert decrypted == original

        # 测试已加密的 key 不会被重复加密
        double_encrypted = encrypt_api_key(encrypted)
        assert double_encrypted == encrypted

    def test_is_garbage_message(self):
        """测试垃圾消息识别"""
        from utils import is_garbage_message

        assert is_garbage_message("你好") == True
        assert is_garbage_message("在吗？") == True
        assert is_garbage_message("hi") == True
        assert is_garbage_message("hello!") == True
        assert is_garbage_message("你是谁？") == True
        assert is_garbage_message("测试") == True
        assert is_garbage_message("???") == True

        # 正常消息
        assert is_garbage_message("今天天气很好") == False
        assert is_garbage_message("我今天工作很忙") == False

    def test_parse_date_range(self):
        """测试日期范围解析"""
        from utils import parse_date_range

        # 单日期
        start, end = parse_date_range("2024-02-24")
        assert start == "2024-02-24"
        assert end is None

        # 日期范围 - 至
        start, end = parse_date_range("2024-02-20至2024-02-25")
        assert start == "2024-02-20"
        assert end == "2024-02-25"

        # 日期范围 - 到
        start, end = parse_date_range("2024-02-20到2024-02-25")
        assert start == "2024-02-20"
        assert end == "2024-02-25"


class TestLogger:
    """日志模块测试"""

    def test_get_logger(self):
        """测试获取日志记录器"""
        from logger import get_logger
        logger1 = get_logger()
        logger2 = get_logger()
        # 应该返回同一实例
        assert logger1 is logger2

    def test_log_methods(self):
        """测试日志方法"""
        from logger import get_logger
        logger = get_logger()
        # 测试各日志级别方法存在
        assert hasattr(logger, 'info')
        assert hasattr(logger, 'warning')
        assert hasattr(logger, 'error')


class TestAgent:
    """Agent 模块测试"""

    def test_agent_init(self):
        """测试 Agent 初始化"""
        from agent import DiaryAgent
        agent = DiaryAgent("test_user")
        assert agent.user_id == "test_user"
        assert agent.memory is not None
        assert agent.diary is not None

    def test_mood_dataclass(self):
        """测试 Mood 数据类"""
        from agent import Mood
        mood = Mood(level=5, name="超开心", description="今天很开心")
        assert mood.level == 5
        assert mood.name == "超开心"


class TestWritingStyle:
    """写作风格模块测试"""

    def test_writing_style_manager(self):
        """测试写作风格管理器"""
        from writing_style import WritingStyleManager
        manager = WritingStyleManager("test_user")
        content = manager.load()
        assert "# 写作风格" in content

    def test_get_writing_style(self):
        """测试获取写作风格"""
        from writing_style import get_writing_style
        style = get_writing_style("test_user")
        assert isinstance(style, str)


class TestUserProfile:
    """用户画像模块测试"""

    def test_user_profile_manager(self):
        """测试用户画像管理器"""
        from user_profile import UserProfileManager
        manager = UserProfileManager("test_user")
        content = manager.load()
        assert "# 用户画像" in content


class TestRetrieval:
    """检索模块测试"""

    def test_extract_keywords(self):
        """测试关键词提取"""
        from retrieval.diary_retriever import _extract_keywords

        keywords = _extract_keywords("今天我和赵璐讨论了项目进展")
        assert "赵璐" in keywords
        assert "项目" in keywords
        assert "讨论" in keywords or "进展" in keywords
        # 停用词应该被过滤
        assert "今天" not in keywords

    def test_extract_entities(self):
        """测试实体提取"""
        from retrieval.diary_retriever import _extract_entities

        entities = _extract_entities("赵璐、王明、小李")
        assert "赵璐" in entities
        assert "王明" in entities

    def test_detect_topic(self):
        """测试话题检测"""
        from retrieval.diary_retriever import _detect_topic

        assert _detect_topic("今天加班到很晚") == "工作"
        assert _detect_topic("和女朋友约会") == "情感"
        assert _detect_topic("去医院看病") == "健康"
        assert _detect_topic("去看电影") == "娱乐"
        assert _detect_topic("随便聊聊") == "其他"

    def test_diary_indexer(self):
        """测试日记索引器"""
        from retrieval.diary_retriever import DiaryIndexer

        indexer = DiaryIndexer("test_user")
        assert indexer.user_id == "test_user"

        # 测试索引日记
        indexer.index_diary(
            "2024-02-24",
            "今天是很开心的一天",
            summary="开心的一天",
            topic="生活",
            mood_level=4
        )

        # 测试搜索
        context = {"query": "开心", "mentioned_entities": [], "current_topic": None}
        results = indexer.search_with_context("开心", context, top_k=3)
        assert len(results) > 0


class TestFunctionTools:
    """Function Tools 模块测试"""

    def test_should_use_functions(self):
        """测试是否使用 Function Call 判断"""
        try:
            import function_tools
        except Exception as e:
            raise AssertionError(f"导入失败: {e}")

        # 情绪关键词
        assert function_tools.should_use_functions("今天被气到了") == True
        assert function_tools.should_use_functions("我很开心") == True

        # 历史关键词
        assert function_tools.should_use_functions("之前的事情") == True
        assert function_tools.should_use_functions("上次我们聊了什么") == True

        # 生成日记
        assert function_tools.should_use_functions("生成日记") == True
        assert function_tools.should_use_functions("帮我写日记") == True

        # 中文字符会被识别为人名，返回 True（这是当前设计）
        # 明确不包含人名的短句
        assert function_tools.should_use_functions("ok") == False

    def test_get_functions_for_provider(self):
        """测试获取函数定义"""
        try:
            import function_tools
        except Exception as e:
            raise AssertionError(f"导入失败: {e}")

        # MiniMax 使用 Anthropic 格式
        funcs = function_tools.get_functions_for_provider("minimax", "")
        assert "input_schema" in funcs[0]

        # OpenAI 使用 type/function 格式
        funcs = function_tools.get_functions_for_provider("openai", "")
        assert "function" in funcs[0]


def run_all_tests():
    """运行所有测试"""
    test_classes = [
        TestConfig,
        TestUtils,
        TestLogger,
        TestAgent,
        TestWritingStyle,
        TestUserProfile,
        TestRetrieval,
        TestFunctionTools,
    ]

    total = 0
    passed = 0
    failed = []

    for cls in test_classes:
        instance = cls()
        for method_name in dir(instance):
            if method_name.startswith("test_"):
                total += 1
                try:
                    getattr(instance, method_name)()
                    passed += 1
                    print(f"✅ {cls.__name__}.{method_name}")
                except Exception as e:
                    import traceback
                    tb = traceback.format_exc()
                    failed.append(f"{cls.__name__}.{method_name}: {str(e)}\n{tb}")
                    print(f"❌ {cls.__name__}.{method_name}: {str(e)}")

    print(f"\n{'='*50}")
    print(f"测试结果: {passed}/{total} 通过")
    if failed:
        print(f"失败 {len(failed)} 项:")
        for f in failed:
            print(f"  - {f}")
        return False
    else:
        print("🎉 所有测试通过!")
        return True


if __name__ == "__main__":
    run_all_tests()
