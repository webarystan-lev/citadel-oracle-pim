"""
🏛️ Citadel Oracle PIM — Тесты Шлюза ConvexBridge
Проверка реактивной синхронизации данных, fallback-режима и CRUD-операций с мокированием ConvexClient.
"""

import os
import json
import unittest
from unittest.mock import patch, MagicMock
from providers.convex_client import ConvexBridge


class TestConvexBridgeFallback(unittest.TestCase):
    """Тестирование автономного (in-memory / fallback) режима при отсутствии подключения к Convex."""

    def setUp(self):
        # Гарантируем отсутствие CONVEX_URL при инициализации
        with patch.dict(os.environ, {}, clear=True):
            self.bridge = ConvexBridge()

    def test_initialization_inactive(self):
        """Проверка, что без CONVEX_URL мост не активен."""
        self.assertFalse(self.bridge.is_active)
        self.assertIsNone(self.bridge.client)
        self.assertFalse(self.bridge.check_connection())

    def test_chats_fallback_safe(self):
        """Проверка безопасного возврата при операциях с чатами."""
        self.assertEqual(self.bridge.load_all_chats(), {})
        self.assertFalse(self.bridge.save_chat("chat-1", {}))
        self.assertFalse(self.bridge.rename_chat("chat-1", "New Title"))
        self.assertFalse(self.bridge.delete_chat("chat-1"))
        self.assertFalse(self.bridge.add_message("chat-1", {"role": "user", "content": "Тест"}))

    def test_notebooks_and_journals_fallback_safe(self):
        """Проверка безопасного возврата при операциях с журналами и блокнотами."""
        self.assertEqual(self.bridge.load_notebooks(), [])
        self.assertFalse(self.bridge.save_notebook({"id": "nb-1", "title": "Тест"}))
        self.assertFalse(self.bridge.delete_notebook("nb-1"))
        self.assertEqual(self.bridge.load_journals(), [])
        self.assertEqual(self.bridge.load_journals_by_notebook("nb-1"), [])
        self.assertFalse(self.bridge.save_journal({"id": "j-1", "date": "2026-09-06", "title": "Запись", "content": "Текст"}))
        self.assertFalse(self.bridge.update_journal({"id": "j-1", "title": "Запись"}))
        self.assertFalse(self.bridge.delete_journal("j-1"))

    def test_projects_notes_vault_fallback_safe(self):
        """Проверка безопасного возврата для проектов, заметок и сейфа."""
        self.assertEqual(self.bridge.load_projects(), [])
        self.assertFalse(self.bridge.save_project({"id": "p-1", "title": "Проект", "description": "Описание"}))
        self.assertFalse(self.bridge.delete_project("p-1"))

        self.assertEqual(self.bridge.load_notes(), [])
        self.assertFalse(self.bridge.save_note({"id": "n-1", "title": "Заметка", "content": "Конспект"}))
        self.assertFalse(self.bridge.delete_note("n-1"))

        self.assertEqual(self.bridge.load_vault(), [])
        self.assertFalse(self.bridge.save_vault_entry({"id": "v-1", "title": "Секрет", "encryptedPayload": "enc"}))
        self.assertFalse(self.bridge.delete_vault_entry("v-1"))


class TestConvexBridgeActive(unittest.TestCase):
    """Тестирование CRUD-методов ConvexBridge с активным мокированным клиентом."""

    def setUp(self):
        # Инициализируем без реального обращения к сети
        with patch.dict(os.environ, {}, clear=True):
            self.bridge = ConvexBridge()
        self.mock_client = MagicMock()
        self.bridge.client = self.mock_client
        self.bridge.is_active = True

    def test_check_connection_success(self):
        """Проверка успешной проверки связи."""
        self.mock_client.query.return_value = []
        self.assertTrue(self.bridge.check_connection())
        self.mock_client.query.assert_called_with("chats:list")

    def test_check_connection_failure(self):
        """Проверка обработки ошибки сети при проверке связи."""
        self.mock_client.query.side_effect = Exception("Convex network timeout")
        self.assertFalse(self.bridge.check_connection())

    def test_load_all_chats(self):
        """Проверка загрузки всех чатов со сбором сообщений и разбором JSON-метаданных."""
        self.mock_client.query.side_effect = [
            # 1-й вызов: chats:list
            [{
                "id": "c1",
                "title": "Свиток 1",
                "provider": "Google Gemini",
                "model": "gemini-2.5-flash",
                "systemPrompt": "Будь верным соратником",
                "temperature": 0.7,
                "maxTokens": 4096
            }],
            # 2-й вызов: messages:listForChat
            [{
                "role": "user",
                "content": "Мир вам!",
                "thinking": "",
                "meta": json.dumps({"source": "unit_test", "timestamp": 12345})
            }, {
                "role": "assistant",
                "content": "И духу твоему!",
                "thinking": "Рассуждение о благословении",
                "meta": ""
            }]
        ]

        chats = self.bridge.load_all_chats()
        self.assertIn("c1", chats)
        chat = chats["c1"]
        self.assertEqual(chat["title"], "Свиток 1")
        self.assertEqual(len(chat["messages"]), 2)
        self.assertEqual(chat["messages"][0]["meta"]["source"], "unit_test")
        self.assertEqual(chat["messages"][1]["thinking"], "Рассуждение о благословении")

    def test_save_chat(self):
        """Проверка сохранения данных чата в Convex."""
        chat_data = {
            "title": "Новый диалог",
            "provider": "Anthropic Claude",
            "model": "claude-3-5-sonnet",
            "system_prompt": "Инструкция",
            "temperature": 0.5,
            "max_tokens": 2048
        }
        res = self.bridge.save_chat("c2", chat_data)
        self.assertTrue(res)
        self.mock_client.mutation.assert_called_with("chats:save", {
            "id": "c2",
            "title": "Новый диалог",
            "provider": "Anthropic Claude",
            "model": "claude-3-5-sonnet",
            "systemPrompt": "Инструкция",
            "temperature": 0.5,
            "maxTokens": 2048
        })

    def test_rename_and_delete_chat(self):
        """Проверка переименования и удаления диалога."""
        self.assertTrue(self.bridge.rename_chat("c1", "Обновленный Свиток"))
        self.mock_client.mutation.assert_called_with("chats:rename", {"id": "c1", "title": "Обновленный Свиток"})

        self.assertTrue(self.bridge.delete_chat("c1"))
        self.mock_client.mutation.assert_called_with("chats:remove", {"id": "c1"})

    def test_add_message(self):
        """Проверка добавления сообщения в диалог."""
        msg = {
            "role": "user",
            "content": "Вопрос о Писании",
            "thinking": "",
            "meta": {"test": True}
        }
        self.assertTrue(self.bridge.add_message("c1", msg))
        self.mock_client.mutation.assert_called_with("messages:add", {
            "chatId": "c1",
            "role": "user",
            "content": "Вопрос о Писании",
            "thinking": "",
            "meta": json.dumps({"test": True})
        })

    def test_notebooks_crud(self):
        """Проверка операций с тематическими блокнотами."""
        self.mock_client.query.return_value = [{"id": "nb-1", "title": "Миссия Шехина"}]
        notebooks = self.bridge.load_notebooks()
        self.assertEqual(len(notebooks), 1)
        self.mock_client.query.assert_called_with("notebooks:listNotebooks")

        self.assertTrue(self.bridge.save_notebook({"id": "nb-2", "title": "AI & WebDev"}))
        self.mock_client.mutation.assert_called_with("notebooks:createNotebook", {
            "id": "nb-2",
            "title": "AI & WebDev",
            "description": "",
            "icon": "📓",
            "categoryType": "GENERAL"
        })

        self.assertTrue(self.bridge.delete_notebook("nb-1"))
        self.mock_client.mutation.assert_called_with("notebooks:deleteNotebook", {"id": "nb-1"})

    def test_journals_crud(self):
        """Проверка операций с записями журнала."""
        self.mock_client.query.return_value = [{"id": "j-1", "title": "Утренняя рефлексия"}]
        journals = self.bridge.load_journals()
        self.assertEqual(len(journals), 1)
        self.mock_client.query.assert_called_with("journals:listJournals")

        journals_nb = self.bridge.load_journals_by_notebook("nb-1")
        self.assertEqual(len(journals_nb), 1)
        self.mock_client.query.assert_called_with("journals:listJournalsByNotebook", {"notebookId": "nb-1"})

        j_data = {
            "id": "j-1",
            "date": "2026-09-06",
            "title": "Рефлексия",
            "content": "Текст",
            "notebookId": "nb-1"
        }
        self.assertTrue(self.bridge.save_journal(j_data))
        self.mock_client.mutation.assert_called_with("journals:createJournal", {
            "id": "j-1",
            "date": "2026-09-06",
            "title": "Рефлексия",
            "content": "Текст",
            "tags": [],
            "category": "Размышление",
            "projectId": "",
            "reflectionQuestions": "",
            "aiSynthesis": "",
            "notebookId": "nb-1"
        })

        self.assertTrue(self.bridge.update_journal(j_data))
        self.mock_client.mutation.assert_called_with("journals:updateJournal", j_data)

        self.assertTrue(self.bridge.delete_journal("j-1"))
        self.mock_client.mutation.assert_called_with("journals:deleteJournal", {"id": "j-1"})

    def test_projects_crud(self):
        """Проверка операций с проектами Цитадели."""
        self.mock_client.query.return_value = [{"id": "p-1", "title": "Citadel Oracle PIM"}]
        projects = self.bridge.load_projects()
        self.assertEqual(len(projects), 1)
        self.mock_client.query.assert_called_with("projects:listProjects")

        p_data = {
            "id": "p-1",
            "title": "Web Arystan",
            "description": "Веб-студия"
        }
        self.assertTrue(self.bridge.save_project(p_data))
        self.mock_client.mutation.assert_called_with("projects:createProject", {
            "id": "p-1",
            "title": "Web Arystan",
            "description": "Веб-студия",
            "status": "Active",
            "category": "Ministry",
            "milestones": "",
            "tags": []
        })

        self.assertTrue(self.bridge.delete_project("p-1"))
        self.mock_client.mutation.assert_called_with("projects:deleteProject", {"id": "p-1"})

    def test_notes_crud(self):
        """Проверка операций с заметками."""
        self.mock_client.query.return_value = [{"id": "n-1", "title": "Богословие благодати"}]
        notes = self.bridge.load_notes()
        self.assertEqual(len(notes), 1)
        self.mock_client.query.assert_called_with("notes:listNotes")

        n_data = {
            "id": "n-1",
            "title": "Заметка",
            "content": "Конспект"
        }
        self.assertTrue(self.bridge.save_note(n_data))
        self.mock_client.mutation.assert_called_with("notes:createNote", {
            "id": "n-1",
            "title": "Заметка",
            "category": "General",
            "content": "Конспект",
            "tags": [],
            "isArchived": False
        })

        self.assertTrue(self.bridge.delete_note("n-1"))
        self.mock_client.mutation.assert_called_with("notes:deleteNote", {"id": "n-1"})

    def test_vault_crud(self):
        """Проверка операций с зашифрованным сейфом ключей."""
        self.mock_client.query.return_value = [{"id": "v-1", "title": "Convex Deploy Token"}]
        vault = self.bridge.load_vault()
        self.assertEqual(len(vault), 1)
        self.mock_client.query.assert_called_with("vault:listVaultEntries")

        v_data = {
            "id": "v-1",
            "title": "API Token",
            "encryptedPayload": "enc_fernet_data"
        }
        self.assertTrue(self.bridge.save_vault_entry(v_data))
        self.mock_client.mutation.assert_called_with("vault:createVaultEntry", {
            "id": "v-1",
            "title": "API Token",
            "secretType": "API_KEY",
            "encryptedPayload": "enc_fernet_data",
            "serviceName": "",
            "note": ""
        })

        self.assertTrue(self.bridge.delete_vault_entry("v-1"))
        self.mock_client.mutation.assert_called_with("vault:deleteVaultEntry", {"id": "v-1"})


if __name__ == "__main__":
    unittest.main()
