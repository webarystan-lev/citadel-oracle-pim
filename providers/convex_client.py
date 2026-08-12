import os
import json
import logging
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ConvexBridge")

class ConvexBridge:
    """
    Высокотехнологичный мост интеграции с Convex DB для Citadel Oracle PIM.
    Обеспечивает реактивную синхронизацию диалогов, журнала, проектов, заметок и зашифрованного сейфа.
    """
    def __init__(self):
        self.convex_url = os.getenv("CONVEX_URL")
        self.client = None
        self.is_active = False

        if not self.convex_url:
            logger.warning("⚠️ Переменная CONVEX_URL не обнаружена в окружении. Мост Convex переведен в автономный (In-Memory) режим.")
            return

        try:
            import sys
            orig_path = list(sys.path)
            
            # Временно удаляем локальные пути и пути корня проекта, чтобы импортировался настоящий пакет convex, а не папка convex/
            sys.path = [
                p for p in sys.path 
                if os.path.abspath(p) not in (
                    os.path.abspath('.'), 
                    os.path.abspath(os.getcwd()), 
                    os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
                )
            ]
            
            from convex import ConvexClient
            
            sys.path = orig_path
            
            self.client = ConvexClient(self.convex_url)
            self.is_active = True
            logger.info(f"✨ Мост Convex успешно инициализирован. Подключение к обители: {self.convex_url}")
        except Exception as e:
            if 'orig_path' in locals():
                sys.path = orig_path
            logger.error(f"🔴 Ошибка при инициализации ConvexClient: {str(e)}")
            self.is_active = False

    def check_connection(self) -> bool:
        """Проверяет работоспособность подключения."""
        if not self.is_active or not self.client:
            return False
        try:
            self.client.query("chats:list")
            return True
        except Exception as e:
            logger.warning(f"⚠️ Сетевой сбой при проверке связи с Convex DB: {str(e)}")
            return False

    # ==================== ЧАТЫ И СООБЩЕНИЯ ====================
    def load_all_chats(self) -> Dict[str, Any]:
        if not self.is_active or not self.client:
            return {}

        try:
            db_chats = self.client.query("chats:list")
            chats_dict = {}

            for chat in db_chats:
                chat_id = chat["id"]
                db_messages = self.client.query("messages:listForChat", {"chatId": chat_id})
                messages_list = []
                
                for msg in db_messages:
                    meta_data = {}
                    if "meta" in msg and msg["meta"]:
                        try:
                            meta_data = json.loads(msg["meta"])
                        except Exception:
                            meta_data = {}

                    messages_list.append({
                        "role": msg["role"],
                        "content": msg["content"],
                        "thinking": msg.get("thinking", ""),
                        "meta": meta_data
                    })

                chats_dict[chat_id] = {
                    "id": chat_id,
                    "title": chat["title"],
                    "provider": chat["provider"],
                    "model": chat["model"],
                    "system_prompt": chat["systemPrompt"],
                    "temperature": float(chat["temperature"]),
                    "max_tokens": int(chat["maxTokens"]),
                    "messages": messages_list
                }
            return chats_dict
        except Exception as e:
            logger.error(f"🔴 Сбой при загрузке чатов из Convex: {str(e)}")
            return {}

    def save_chat(self, chat_id: str, chat_data: Dict[str, Any]) -> bool:
        if not self.is_active or not self.client:
            return False
        try:
            self.client.mutation("chats:save", {
                "id": chat_id,
                "title": chat_data.get("title", "🏛️ Новый диалог"),
                "provider": chat_data.get("provider", "Google Gemini"),
                "model": chat_data.get("model", "gemini-2.5-flash"),
                "systemPrompt": chat_data.get("system_prompt", ""),
                "temperature": float(chat_data.get("temperature", 0.7)),
                "maxTokens": float(chat_data.get("max_tokens", 4096))
            })
            return True
        except Exception as e:
            logger.error(f"🔴 Ошибка chats:save: {str(e)}")
            return False

    def rename_chat(self, chat_id: str, title: str) -> bool:
        if not self.is_active or not self.client:
            return False
        try:
            self.client.mutation("chats:rename", {"id": chat_id, "title": title})
            return True
        except Exception as e:
            logger.error(f"🔴 Ошибка chats:rename: {str(e)}")
            return False

    def delete_chat(self, chat_id: str) -> bool:
        if not self.is_active or not self.client:
            return False
        try:
            self.client.mutation("chats:remove", {"id": chat_id})
            return True
        except Exception as e:
            logger.error(f"🔴 Ошибка chats:remove: {str(e)}")
            return False

    def add_message(self, chat_id: str, message: Dict[str, Any]) -> bool:
        if not self.is_active or not self.client:
            return False
        try:
            meta_str = json.dumps(message.get("meta", {})) if message.get("meta") else ""
            self.client.mutation("messages:add", {
                "chatId": chat_id,
                "role": message["role"],
                "content": message["content"],
                "thinking": message.get("thinking", ""),
                "meta": meta_str
            })
            return True
        except Exception as e:
            logger.error(f"🔴 Ошибка messages:add: {str(e)}")
            return False

    # ==================== ТЕМАТИЧЕСКИЕ ЖУРНАЛЫ / БЛОКНОТЫ (NOTEBOOKS) ====================
    def load_notebooks(self) -> List[Dict[str, Any]]:
        if not self.is_active or not self.client:
            return []
        try:
            return self.client.query("notebooks:listNotebooks")
        except Exception as e:
            logger.error(f"🔴 Ошибка notebooks:listNotebooks: {str(e)}")
            return []

    def save_notebook(self, notebook_data: Dict[str, Any]) -> bool:
        if not self.is_active or not self.client:
            return False
        try:
            self.client.mutation("notebooks:createNotebook", {
                "id": notebook_data["id"],
                "title": notebook_data["title"],
                "description": notebook_data.get("description", ""),
                "icon": notebook_data.get("icon", "📓"),
                "categoryType": notebook_data.get("categoryType", "GENERAL")
            })
            return True
        except Exception as e:
            logger.error(f"🔴 Ошибка notebooks:createNotebook: {str(e)}")
            return False

    def delete_notebook(self, notebook_id: str) -> bool:
        if not self.is_active or not self.client:
            return False
        try:
            self.client.mutation("notebooks:deleteNotebook", {"id": notebook_id})
            return True
        except Exception as e:
            logger.error(f"🔴 Ошибка notebooks:deleteNotebook: {str(e)}")
            return False

    # ==================== ЗАПИСИ ЖУРНАЛОВ (JOURNALS) ====================
    def load_journals(self) -> List[Dict[str, Any]]:
        if not self.is_active or not self.client:
            return []
        try:
            return self.client.query("journals:listJournals")
        except Exception as e:
            logger.error(f"🔴 Ошибка journals:listJournals: {str(e)}")
            return []

    def load_journals_by_notebook(self, notebook_id: str) -> List[Dict[str, Any]]:
        if not self.is_active or not self.client:
            return []
        try:
            return self.client.query("journals:listJournalsByNotebook", {"notebookId": notebook_id})
        except Exception as e:
            logger.error(f"🔴 Ошибка journals:listJournalsByNotebook: {str(e)}")
            # Фолбэк на фильтрацию по клиентской стороне
            all_j = self.load_journals()
            return [j for j in all_j if j.get("notebookId") == notebook_id]

    def save_journal(self, journal_data: Dict[str, Any]) -> bool:
        if not self.is_active or not self.client:
            return False
        try:
            payload = {
                "id": journal_data["id"],
                "date": journal_data["date"],
                "title": journal_data["title"],
                "content": journal_data["content"],
                "tags": journal_data.get("tags", []),
                "category": journal_data.get("category", "Размышление"),
                "projectId": journal_data.get("projectId", ""),
                "reflectionQuestions": journal_data.get("reflectionQuestions", ""),
                "aiSynthesis": journal_data.get("aiSynthesis", "")
            }
            if journal_data.get("notebookId"):
                payload["notebookId"] = journal_data["notebookId"]

            self.client.mutation("journals:createJournal", payload)
            return True
        except Exception as e:
            logger.error(f"🔴 Ошибка journals:createJournal: {str(e)}")
            return False

    def update_journal(self, journal_data: Dict[str, Any]) -> bool:
        if not self.is_active or not self.client:
            return False
        try:
            payload: Dict[str, Any] = {"id": journal_data["id"]}
            if "notebookId" in journal_data: payload["notebookId"] = journal_data["notebookId"]
            if "date" in journal_data: payload["date"] = journal_data["date"]
            if "title" in journal_data: payload["title"] = journal_data["title"]
            if "content" in journal_data: payload["content"] = journal_data["content"]
            if "tags" in journal_data: payload["tags"] = journal_data["tags"]
            if "category" in journal_data: payload["category"] = journal_data["category"]
            if "projectId" in journal_data: payload["projectId"] = journal_data["projectId"]
            if "reflectionQuestions" in journal_data: payload["reflectionQuestions"] = journal_data["reflectionQuestions"]
            if "aiSynthesis" in journal_data: payload["aiSynthesis"] = journal_data["aiSynthesis"]

            self.client.mutation("journals:updateJournal", payload)
            return True
        except Exception as e:
            logger.error(f"🔴 Ошибка journals:updateJournal: {str(e)}")
            return False

    def delete_journal(self, entry_id: str) -> bool:
        if not self.is_active or not self.client:
            return False
        try:
            self.client.mutation("journals:deleteJournal", {"id": entry_id})
            return True
        except Exception as e:
            logger.error(f"🔴 Ошибка journals:deleteJournal: {str(e)}")
            return False

    # ==================== ПРОЕКТЫ (PROJECTS) ====================
    def load_projects(self) -> List[Dict[str, Any]]:
        if not self.is_active or not self.client:
            return []
        try:
            return self.client.query("projects:listProjects")
        except Exception as e:
            logger.error(f"🔴 Ошибка projects:listProjects: {str(e)}")
            return []

    def save_project(self, project_data: Dict[str, Any]) -> bool:
        if not self.is_active or not self.client:
            return False
        try:
            self.client.mutation("projects:createProject", {
                "id": project_data["id"],
                "title": project_data["title"],
                "description": project_data["description"],
                "status": project_data.get("status", "Active"),
                "category": project_data.get("category", "Ministry"),
                "milestones": project_data.get("milestones", ""),
                "tags": project_data.get("tags", [])
            })
            return True
        except Exception as e:
            logger.error(f"🔴 Ошибка projects:createProject: {str(e)}")
            return False

    def delete_project(self, project_id: str) -> bool:
        if not self.is_active or not self.client:
            return False
        try:
            self.client.mutation("projects:deleteProject", {"id": project_id})
            return True
        except Exception as e:
            logger.error(f"🔴 Ошибка projects:deleteProject: {str(e)}")
            return False

    # ==================== ЗАМЕТКИ (NOTES) ====================
    def load_notes(self) -> List[Dict[str, Any]]:
        if not self.is_active or not self.client:
            return []
        try:
            return self.client.query("notes:listNotes")
        except Exception as e:
            logger.error(f"🔴 Ошибка notes:listNotes: {str(e)}")
            return []

    def save_note(self, note_data: Dict[str, Any]) -> bool:
        if not self.is_active or not self.client:
            return False
        try:
            self.client.mutation("notes:createNote", {
                "id": note_data["id"],
                "title": note_data["title"],
                "category": note_data.get("category", "General"),
                "content": note_data["content"],
                "tags": note_data.get("tags", []),
                "isArchived": note_data.get("isArchived", False)
            })
            return True
        except Exception as e:
            logger.error(f"🔴 Ошибка notes:createNote: {str(e)}")
            return False

    def delete_note(self, note_id: str) -> bool:
        if not self.is_active or not self.client:
            return False
        try:
            self.client.mutation("notes:deleteNote", {"id": note_id})
            return True
        except Exception as e:
            logger.error(f"🔴 Ошибка notes:deleteNote: {str(e)}")
            return False

    # ==================== СЕЙФ КЛЮЧЕЙ (VAULT) ====================
    def load_vault(self) -> List[Dict[str, Any]]:
        if not self.is_active or not self.client:
            return []
        try:
            return self.client.query("vault:listVaultEntries")
        except Exception as e:
            logger.error(f"🔴 Ошибка vault:listVaultEntries: {str(e)}")
            return []

    def save_vault_entry(self, vault_data: Dict[str, Any]) -> bool:
        if not self.is_active or not self.client:
            return False
        try:
            self.client.mutation("vault:createVaultEntry", {
                "id": vault_data["id"],
                "title": vault_data["title"],
                "secretType": vault_data.get("secretType", "API_KEY"),
                "encryptedPayload": vault_data["encryptedPayload"],
                "serviceName": vault_data.get("serviceName", ""),
                "note": vault_data.get("note", "")
            })
            return True
        except Exception as e:
            logger.error(f"🔴 Ошибка vault:createVaultEntry: {str(e)}")
            return False

    def delete_vault_entry(self, entry_id: str) -> bool:
        if not self.is_active or not self.client:
            return False
        try:
            self.client.mutation("vault:deleteVaultEntry", {"id": entry_id})
            return True
        except Exception as e:
            logger.error(f"🔴 Ошибка vault:deleteVaultEntry: {str(e)}")
            return False
