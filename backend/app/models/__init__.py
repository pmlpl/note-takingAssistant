# 以下导入仅为把模型注册进 Base.metadata（create_all 建表用），显式 re-export
from .ai_conversation import AIConversationDB as AIConversationDB
from .ai_conversation import AIMessageDB as AIMessageDB
from .kg import KGConceptDB as KGConceptDB
from .kg import KGRelationDB as KGRelationDB
from .kg import KGStatusDB as KGStatusDB
from .note_chunk import NoteChunkDB as NoteChunkDB
