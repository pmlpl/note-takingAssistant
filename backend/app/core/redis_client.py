"""
Redis 客户端配置和连接管理
用于缓存最近笔记等数据
"""
import redis
from app.core.config import settings
import json
from typing import Optional, List
from app.core.logger import app_logger as logger


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
            logger.info(f"⚠️ Redis 连接失败: {e}")
            logger.info("💡 提示：请确保已安装并启动 Redis 服务")
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
        logger.info("⚠️ Redis 不可用，跳过缓存")
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
        logger.info(f"❌ 缓存笔记失败: {e}")


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
        logger.info(f"❌ 从最近笔记移除 id={note_id} 失败: {e}")


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
        logger.info("⚠️ Redis 不可用，跳过缓存")
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
        logger.info(f"❌ 批量缓存笔记失败: {e}")


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
                logger.info(f"⚠️ 解析笔记数据失败: {e}")
                continue
        
        return notes
    except Exception as e:
        logger.info(f"❌ 获取最近笔记失败: {e}")
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
        logger.info(f"❌ 清除缓存失败: {e}")


# ═══════════════════════════════════════════
# JWT Token 黑名单（撤销机制）
# ═══════════════════════════════════════════

BLACKLIST_PREFIX = "token_blacklist:"


def blacklist_token(jti_or_token: str, ttl_seconds: int) -> bool:
    """
    将 jti 加入 Redis 黑名单（ttl_seconds 应等于 token 剩余有效期）。
    入参优先使用 jti（短而稳定），但也兼容老调用直接传入原 token 字符串。
    """
    client = redis_client.client
    if not client:
        return False
    try:
        # 取 jti 作为 key：如果入参包含 ':'，说明已是 jti；否则按旧 token 做一次 hash 降级
        if ":" in jti_or_token:
            key = f"{BLACKLIST_PREFIX}{jti_or_token}"
        else:
            key = f"{BLACKLIST_PREFIX}{hash(jti_or_token)}"
        client.setex(key, max(ttl_seconds, 1), "1")
        return True
    except Exception as e:
        logger.info(f"❌ 令牌加入黑名单失败: {e}")
        return False


def is_token_blacklisted(token: str) -> bool:
    """
    检查 jti 是否在 Redis 黑名单中。
    安全策略：Redis 不可用时返回 True（拒绝），避免在 Redis 重启窗口期绕过撤销。
    """
    client = redis_client.client
    if not client:
        # 降级为拒绝：Redis 挂了就不能确认 token 没被撤销，保守拒绝
        return True
    try:
        # 从 token 提取 jti（本地 decode，不依赖网络）
        from app.core.security import get_jti_from_token
        jti = get_jti_from_token(token)
        if not jti:
            # 如果 token 根本没有 jti（老 token 格式），降级为用 hash(token) 作 key
            key = f"{BLACKLIST_PREFIX}{hash(token)}"
        else:
            key = f"{BLACKLIST_PREFIX}{jti}"
        return client.exists(key) > 0
    except Exception as e:
        logger.info(f"⚠️ 黑名单查询失败（保守拒绝）: {e}")
        return True


def _rate_limit_bump(key: str, window_seconds: int) -> int | None:
    """
    速率限制原语：对 key 做 INCR，并在首次写入时设置 TTL=window_seconds。
    返回当前窗口内的累计计数；Redis 不可用时返回 None。

    注意：这是一个「近似滑动窗口」——在 TTL 到期前计数累加，到期后自动归零。
    足够防御暴力破解与高频滥用，实现成本远低于精确滑动窗口。
    """
    client = redis_client.client
    if not client:
        return None
    try:
        # 先 INCR，若返回 1 说明是 key 新建 → 需要设置 TTL
        current = client.incr(key)
        if current == 1:
            client.expire(key, window_seconds)
        return int(current)
    except Exception as e:
        logger.info(f"⚠️ 速率限制计数失败（降级放行）: {e}")
        return None


# ═══════════════════════════════════════════
# 异步安全包装：在线程池中执行同步 Redis 调用，避免阻塞事件循环
# ═══════════════════════════════════════════

import asyncio as _asyncio


async def _run_in_pool(func, *args):
    """在默认线程池中运行同步函数，返回其结果，失败返回 None。"""
    loop = _asyncio.get_event_loop()
    try:
        return await loop.run_in_executor(None, func, *args)
    except Exception as e:
        logger.info(f"⚠️ Redis 线程池调用失败: {e}")
        return None


async def cache_recent_note_async(user_id: int, note_data: dict) -> None:
    await _run_in_pool(cache_recent_note, user_id, note_data)


async def get_recent_notes_async(user_id: int, limit: int = 20) -> list:
    return (await _run_in_pool(get_recent_notes, user_id, limit)) or []


async def batch_cache_recent_notes_async(user_id: int, notes_data: list) -> None:
    await _run_in_pool(batch_cache_recent_notes, user_id, notes_data)


async def clear_recent_notes_async(user_id: int) -> None:
    await _run_in_pool(clear_recent_notes, user_id)


async def remove_recent_note_by_id_async(user_id: int, note_id: int) -> None:
    await _run_in_pool(remove_recent_note_by_id, user_id, note_id)
