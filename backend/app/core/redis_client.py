"""
Redis 客户端配置和连接管理
用于缓存最近笔记等数据
"""
import redis
from app.core.config import settings
import json
from typing import Optional, List


class RedisClient:
    """Redis 客户端单例类"""
    
    _instance = None
    _client = None
    
    def __new__(cls):
        """单例模式，确保只有一个Redis连接实例"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_redis()
        return cls._instance
    
    def _init_redis(self):
        """初始化Redis连接"""
        try:
            # 构建Redis连接参数，只有当密码不为None时才添加
            redis_params = {
                'host': settings.REDIS_HOST,
                'port': settings.REDIS_PORT,
                'db': settings.REDIS_DB,
                'decode_responses': True,  # 自动解码为字符串
                'socket_connect_timeout': 5,
                'socket_timeout': 5
            }
            
            # 只有当密码存在时才添加到参数中
            if settings.REDIS_PASSWORD is not None:
                redis_params['password'] = settings.REDIS_PASSWORD
            
            self._client = redis.Redis(**redis_params)
            # 测试连接
            self._client.ping()
        except Exception as e:
            print(f"⚠️ Redis 连接失败: {e}")
            print("💡 提示：请确保已安装并启动 Redis 服务")
            self._client = None
    
    @property
    def client(self):
        """获取Redis客户端实例"""
        return self._client
    
    def is_available(self):
        """检查Redis是否可用"""
        return self._client is not None


# 创建全局Redis客户端实例
redis_client = RedisClient()


def get_redis():
    """
    获取Redis客户端（依赖注入用）
    Returns:
        redis.Redis: Redis客户端实例
    """
    return redis_client.client


def cache_recent_note(user_id: int, note_data: dict):
    """
    缓存用户的最近笔记（单个笔记）
    注意：此函数用于增量添加，如果要批量更新顺序，请使用 batch_cache_recent_notes
    
    Args:
        user_id: 用户ID
        note_data: 笔记数据字典，包含 id, title, content, created_at, updated_at, user_id 等字段
    """
    client = redis_client.client
    if not client:
        print("⚠️ Redis 不可用，跳过缓存")
        return
    
    try:
        # Redis key格式: recent_notes:{user_id}
        key = f"recent_notes:{user_id}"
        
        # 确保包含 user_id 字段（NoteResponse 必需）
        note_data['user_id'] = user_id
        
        # 将笔记数据转为JSON字符串
        note_json = json.dumps(note_data, ensure_ascii=False, default=str)
        
        # 检查是否已存在该笔记，如果存在先移除
        existing_notes = client.lrange(key, 0, -1)
        for existing_note_json in existing_notes:
            try:
                existing_note = json.loads(existing_note_json)
                if existing_note.get('id') == note_data.get('id'):
                    client.lrem(key, 1, existing_note_json)
                    break
            except:
                continue
        
        # 从左侧推入（最新笔记在最前面）
        client.lpush(key, note_json)
        
        # 只保留最近20个笔记
        client.ltrim(key, 0, 19)
        
        # 设置过期时间（7天）
        client.expire(key, 7 * 24 * 60 * 60)

    except Exception as e:
        print(f"❌ 缓存笔记失败: {e}")


def remove_recent_note_by_id(user_id: int, note_id: int) -> None:
    """
    从「最近笔记」Redis 列表中移除指定笔记 id（例如覆盖导入已删库中旧笔记，但列表里仍留着旧 id）。
    保持其余条目的相对顺序不变。
    """
    client = redis_client.client
    if not client:
        return
    try:
        key = f"recent_notes:{user_id}"
        notes_json = client.lrange(key, 0, -1)
        kept: List[str] = []
        for nj in notes_json:
            try:
                if json.loads(nj).get("id") == note_id:
                    continue
            except (json.JSONDecodeError, TypeError):
                pass
            kept.append(nj)
        if len(kept) == len(notes_json):
            return
        pipe = client.pipeline()
        pipe.delete(key)
        for nj in reversed(kept):
            pipe.lpush(key, nj)
        if kept:
            pipe.expire(key, 7 * 24 * 60 * 60)
        pipe.execute()
    except Exception as e:
        print(f"❌ 从最近笔记移除 id={note_id} 失败: {e}")


def batch_cache_recent_notes(user_id: int, notes_data: List[dict]):
    """
    批量缓存最近笔记（按指定顺序）
    会完全替换现有的缓存
    
    Args:
        user_id: 用户ID
        notes_data: 笔记数据列表，按从新到旧的顺序排列
    """
    client = redis_client.client
    if not client:
        print("⚠️ Redis 不可用，跳过缓存")
        return
    
    try:
        key = f"recent_notes:{user_id}"
        
        # 清除旧缓存
        client.delete(key)
        
        # 按顺序批量插入（从最旧到最新，这样最新的会在左边）
        # 所以要反转列表
        reversed_notes = list(reversed(notes_data[:20]))  # 最多20个
        
        for note_data in reversed_notes:
            # 确保包含 user_id 字段
            note_data['user_id'] = user_id
            note_json = json.dumps(note_data, ensure_ascii=False, default=str)
            client.lpush(key, note_json)
        
        # 设置过期时间（7天）
        client.expire(key, 7 * 24 * 60 * 60)

    except Exception as e:
        print(f"❌ 批量缓存笔记失败: {e}")


def get_recent_notes(user_id: int, limit: int = 20) -> List[dict]:
    """
    获取用户的最近笔记列表
    
    Args:
        user_id: 用户ID
        limit: 返回数量限制，默认20个
    
    Returns:
        List[dict]: 最近笔记列表
    """
    client = redis_client.client
    if not client:
        return []
    
    try:
        key = f"recent_notes:{user_id}"
        # 获取列表中的所有笔记
        notes_json = client.lrange(key, 0, limit - 1)
        
        # 解析JSON
        notes = []
        for note_json in notes_json:
            try:
                note = json.loads(note_json)
                notes.append(note)
            except json.JSONDecodeError as e:
                print(f"⚠️ 解析笔记数据失败: {e}")
                continue
        
        return notes
    except Exception as e:
        print(f"❌ 获取最近笔记失败: {e}")
        return []


def clear_recent_notes(user_id: int):
    """
    清除用户的最近笔记缓存
    
    Args:
        user_id: 用户ID
    """
    client = redis_client.client
    if not client:
        return
    
    try:
        key = f"recent_notes:{user_id}"
        client.delete(key)
    except Exception as e:
        print(f"❌ 清除缓存失败: {e}")


# ═══════════════════════════════════════════
# JWT Token 黑名单（撤销机制）
# ═══════════════════════════════════════════

BLACKLIST_PREFIX = "token_blacklist:"


def blacklist_token(token: str, ttl_seconds: int) -> bool:
    """
    将 JWT 令牌加入 Redis 黑名单。
    令牌在 ttl_seconds 秒后自动从 Redis 删除（与令牌过期时间对齐），
    所以黑名单不会无限膨胀。

    Args:
        token:  完整的 JWT 令牌字符串
        ttl_seconds: 黑名单保留秒数（应设为令牌剩余有效时间）

    Returns:
        bool: 是否成功加入黑名单
    """
    client = redis_client.client
    if not client:
        return False
    try:
        key = f"{BLACKLIST_PREFIX}{token}"
        client.setex(key, ttl_seconds, "1")
        return True
    except Exception as e:
        print(f"❌ 令牌加入黑名单失败: {e}")
        return False


def is_token_blacklisted(token: str) -> bool:
    """
    检查令牌是否在黑名单中。

    Args:
        token: 完整的 JWT 令牌字符串

    Returns:
        bool: True = 已被撤销，不应放行
    """
    client = redis_client.client
    if not client:
        # Redis 不可用时，降级为不拦截（保持服务可用）
        return False
    try:
        key = f"{BLACKLIST_PREFIX}{token}"
        return client.exists(key) > 0
    except Exception as e:
        print(f"⚠️ 黑名单查询失败，降级放行: {e}")
        return False
