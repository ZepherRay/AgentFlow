from typing import List, Dict, Optional
from datetime import datetime
from app.db.session import get_sync_engine, SyncSessionLocal
from app.models.conversation import Conversation, ChatMessage


class ConversationMemory:
    def __init__(self, session_id: str, max_messages: int = 50):
        self.session_id = session_id
        self.max_messages = max_messages
        self.messages: list[dict] = []
        self._load_from_db()

    def add_message(self, role: str, content: str, is_thinking: bool = False):
        msg = {"role": role, "content": content, "is_thinking": is_thinking, "timestamp": datetime.utcnow().isoformat()}
        self.messages.append(msg)
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
        self._save_to_db(role, content, is_thinking)

    def get_messages(self, include_thinking: bool = True) -> List[Dict]:
        return [m for m in self.messages if include_thinking or not m.get("is_thinking")]

    def get_context(self, limit: int = 20) -> List[Dict]:
        recent = self.messages[-limit:]
        return [{"role": m["role"], "content": m["content"]} for m in recent]

    def clear(self):
        self.messages = []
        self._delete_from_db()

    def archive(self):
        """Archive this session so it appears in history sidebar (creates Conversation row)."""
        session = SyncSessionLocal(bind=get_sync_engine())
        try:
            exists = session.query(Conversation).filter(Conversation.session_id == self.session_id).first()
            if not exists:
                title = ""
                for m in self.messages:
                    if m["role"] == "user":
                        title = m["content"][:100]
                        break
                session.add(Conversation(session_id=self.session_id, title=title))
                session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()

    def _load_from_db(self):
        session = SyncSessionLocal(bind=get_sync_engine())
        try:
            rows = (
                session.query(ChatMessage)
                .filter(ChatMessage.session_id == self.session_id)
                .order_by(ChatMessage.id)
                .all()
            )
            self.messages = [
                {
                    "role": r.role,
                    "content": r.content,
                    "is_thinking": r.is_thinking,
                    "timestamp": r.timestamp.isoformat() if r.timestamp else "",
                }
                for r in rows
            ]
        except Exception:
            self.messages = []
        finally:
            session.close()

    def _save_to_db(self, role: str, content: str, is_thinking: bool):
        """Save ChatMessage only — Conversation row created separately on archive()."""
        session = SyncSessionLocal(bind=get_sync_engine())
        try:
            session.add(ChatMessage(
                session_id=self.session_id,
                role=role,
                content=content,
                is_thinking=is_thinking,
                timestamp=datetime.utcnow(),
            ))
            session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()

    def _delete_from_db(self):
        session = SyncSessionLocal(bind=get_sync_engine())
        try:
            session.query(ChatMessage).filter(ChatMessage.session_id == self.session_id).delete()
            session.query(Conversation).filter(Conversation.session_id == self.session_id).delete()
            session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()


class MemoryManager:
    _instances: Dict[str, ConversationMemory] = {}

    @classmethod
    def get_session(cls, session_id: str, max_messages: int = 50) -> ConversationMemory:
        if session_id not in cls._instances:
            cls._instances[session_id] = ConversationMemory(session_id, max_messages)
        return cls._instances[session_id]

    @classmethod
    def clear_session(cls, session_id: str):
        if session_id in cls._instances:
            cls._instances[session_id].clear()
            del cls._instances[session_id]

    @classmethod
    def archive_session(cls, session_id: str):
        if session_id in cls._instances:
            cls._instances[session_id].archive()
        else:
            ConversationMemory(session_id).archive()

    @classmethod
    def list_sessions(cls) -> List[Dict]:
        """Return all sessions: archived (Conversation) + orphan (ChatMessage without Conversation)."""
        session = SyncSessionLocal(bind=get_sync_engine())
        try:
            from sqlalchemy import text
            sql = text("""
                SELECT session_id, title FROM (
                    SELECT c.session_id, c.title
                    FROM conversations c
                    UNION
                    SELECT DISTINCT m.session_id, NULL AS title
                    FROM chat_messages m
                    WHERE m.session_id NOT IN (SELECT session_id FROM conversations)
                ) all_s
                ORDER BY session_id DESC
            """)
            rows = session.execute(sql).fetchall()
            return [{"session_id": r[0], "title": r[1] or ""} for r in rows]
        except Exception:
            return []
        finally:
            session.close()
