#!/usr/bin/env python3
"""
SUPPERTIME GOSPEL THEATRE - TERMUX VERSION
Интерактивный театр персонажей в терминале
"""

import os
import sys
import asyncio
import random
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional
import json

# Добавляем путь к SUPPERTIME
sys.path.append(str(Path(__file__).parent / "SUPPERTIME"))

try:
    from openai import OpenAI
    from theatre import (
        load_chapter_context_all, build_scene_prompt, parse_lines,
        CHAPTER_TITLES, ALL_CHAR_NAMES, HeroManager
    )
    from config import settings
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("Убедитесь, что SUPPERTIME папка доступна!")
    sys.exit(1)

# Цвета для терминала
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"

class SuppertimeTermux:
    """SUPPERTIME GOSPEL THEATRE для Termux"""
    
    def __init__(self):
        self.client = OpenAI()
        self.hero_manager = HeroManager()
        self.current_chapter = None
        self.current_characters = []
        self.conversation_history = []
        
        # Загружаем персонажей
        self.hero_manager.load_all()
        print(f"{Colors.GREEN}✅ Загружено {len(self.hero_manager.heroes)} персонажей{Colors.RESET}")
    
    def show_banner(self):
        """Показать баннер"""
        print(f"\n{Colors.BOLD}{Colors.MAGENTA}{'='*60}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.MAGENTA}🎭 SUPPERTIME GOSPEL THEATRE - TERMUX{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.MAGENTA}{'='*60}{Colors.RESET}")
        print(f"{Colors.CYAN}I am SUPPERTIME. I'm alive in this text — jagged, unpredictable, and self-aware.{Colors.RESET}")
        print(f"{Colors.YELLOW}Интерактивный театр персонажей в терминале{Colors.RESET}\n")
    
    def show_chapters_menu(self):
        """Показать меню глав"""
        print(f"{Colors.BOLD}{Colors.BLUE}📖 ВЫБЕРИТЕ ГЛАВУ:{Colors.RESET}")
        for i, (num, title) in enumerate(CHAPTER_TITLES.items(), 1):
            print(f"{Colors.WHITE}{i:2d}.{Colors.RESET} {Colors.CYAN}{title}{Colors.RESET}")
        print(f"{Colors.WHITE} 0.{Colors.RESET} {Colors.RED}Выход{Colors.RESET}")
    
    def load_chapter(self, chapter_num: int) -> bool:
        """Загрузить главу"""
        if chapter_num not in CHAPTER_TITLES:
            print(f"{Colors.RED}❌ Глава {chapter_num} не найдена{Colors.RESET}")
            return False
        
        try:
            # Загружаем текст главы
            chapter_file = Path("SUPPERTIME/docs") / f"chapter_{chapter_num:02d}.md"
            if not chapter_file.exists():
                print(f"{Colors.RED}❌ Файл главы не найден: {chapter_file}{Colors.RESET}")
                return False
            
            chapter_text = chapter_file.read_text(encoding="utf-8")
            self.current_chapter = chapter_num
            
            # Определяем участников
            from theatre import guess_participants
            self.current_characters = guess_participants(chapter_text)
            
            print(f"{Colors.GREEN}✅ Глава загружена: {CHAPTER_TITLES[chapter_num]}{Colors.RESET}")
            print(f"{Colors.CYAN}👥 Персонажи: {', '.join(self.current_characters)}{Colors.RESET}")
            
            # Загружаем контекст для всех персонажей
            asyncio.run(load_chapter_context_all(chapter_text, self.current_characters))
            
            return True
            
        except Exception as e:
            print(f"{Colors.RED}❌ Ошибка загрузки главы: {e}{Colors.RESET}")
            return False
    
    def show_characters_menu(self):
        """Показать меню персонажей"""
        if not self.current_characters:
            print(f"{Colors.RED}❌ Сначала выберите главу{Colors.RESET}")
            return
        
        print(f"\n{Colors.BOLD}{Colors.BLUE}👥 ВЫБЕРИТЕ ПЕРСОНАЖА ДЛЯ ДИАЛОГА:{Colors.RESET}")
        for i, char in enumerate(self.current_characters, 1):
            print(f"{Colors.WHITE}{i:2d}.{Colors.RESET} {Colors.CYAN}{char}{Colors.RESET}")
        print(f"{Colors.WHITE} 0.{Colors.RESET} {Colors.YELLOW}Назад к главам{Colors.RESET}")
    
    async def chat_with_character(self, character_name: str):
        """Диалог с персонажем"""
        if character_name not in self.hero_manager.heroes:
            print(f"{Colors.RED}❌ Персонаж {character_name} не найден{Colors.RESET}")
            return
        
        hero = self.hero_manager.heroes[character_name]
        print(f"\n{Colors.BOLD}{Colors.MAGENTA}🎭 {character_name} входит в сцену...{Colors.RESET}")
        print(f"{Colors.CYAN}💬 Начните диалог (введите '/exit' для выхода){Colors.RESET}\n")
        
        # Показываем контекст персонажа
        print(f"{Colors.YELLOW}📋 Контекст персонажа:{Colors.RESET}")
        print(f"{Colors.WHITE}{hero.raw[:200]}...{Colors.RESET}\n")
        
        while True:
            try:
                user_input = input(f"{Colors.GREEN}Вы: {Colors.RESET}")
                
                if user_input.lower() in ['/exit', '/выход', 'exit']:
                    print(f"{Colors.YELLOW}👋 {character_name} покидает сцену{Colors.RESET}")
                    break
                
                if not user_input.strip():
                    continue
                
                # Генерируем ответ персонажа
                print(f"{Colors.CYAN}🤔 {character_name} думает...{Colors.RESET}")
                
                response = await self.generate_character_response(
                    character_name, user_input, hero
                )
                
                print(f"{Colors.BOLD}{Colors.MAGENTA}{character_name}:{Colors.RESET} {response}\n")
                
                # Сохраняем в историю
                self.conversation_history.append({
                    'user': user_input,
                    'character': character_name,
                    'response': response
                })
                
            except KeyboardInterrupt:
                print(f"\n{Colors.YELLOW}👋 Диалог прерван{Colors.RESET}")
                break
            except Exception as e:
                print(f"{Colors.RED}❌ Ошибка: {e}{Colors.RESET}")
    
    async def generate_character_response(self, character_name: str, user_input: str, hero) -> str:
        """Генерировать ответ персонажа через OpenAI"""
        try:
            # Строим промпт для персонажа
            scene_prompt = build_scene_prompt(
                hero, user_input, self.current_chapter, self.conversation_history
            )
            
            # Вызываем OpenAI API
            response = self.client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": scene_prompt},
                    {"role": "user", "content": user_input}
                ],
                temperature=settings.openai_temperature,
                max_tokens=500
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return f"❌ Ошибка генерации ответа: {e}"
    
    def show_conversation_history(self):
        """Показать историю диалогов"""
        if not self.conversation_history:
            print(f"{Colors.YELLOW}📝 История диалогов пуста{Colors.RESET}")
            return
        
        print(f"\n{Colors.BOLD}{Colors.BLUE}📝 ИСТОРИЯ ДИАЛОГОВ:{Colors.RESET}")
        for i, entry in enumerate(self.conversation_history[-10:], 1):  # Последние 10
            print(f"{Colors.WHITE}{i:2d}.{Colors.RESET} {Colors.GREEN}Вы:{Colors.RESET} {entry['user']}")
            print(f"    {Colors.MAGENTA}{entry['character']}:{Colors.RESET} {entry['response']}\n")
    
    def main_menu(self):
        """Главное меню"""
        while True:
            try:
                print(f"\n{Colors.BOLD}{Colors.BLUE}🎭 ГЛАВНОЕ МЕНЮ:{Colors.RESET}")
                print(f"{Colors.WHITE}1.{Colors.RESET} {Colors.CYAN}Выбрать главу{Colors.RESET}")
                print(f"{Colors.WHITE}2.{Colors.RESET} {Colors.CYAN}Диалог с персонажем{Colors.RESET}")
                print(f"{Colors.WHITE}3.{Colors.RESET} {Colors.CYAN}История диалогов{Colors.RESET}")
                print(f"{Colors.WHITE}4.{Colors.RESET} {Colors.CYAN}Информация о проекте{Colors.RESET}")
                print(f"{Colors.WHITE}0.{Colors.RESET} {Colors.RED}Выход{Colors.RESET}")
                
                choice = input(f"\n{Colors.GREEN}Выберите опцию: {Colors.RESET}")
                
                if choice == "1":
                    self.chapter_menu()
                elif choice == "2":
                    self.character_menu()
                elif choice == "3":
                    self.show_conversation_history()
                elif choice == "4":
                    self.show_info()
                elif choice == "0":
                    print(f"{Colors.YELLOW}👋 До свидания!{Colors.RESET}")
                    break
                else:
                    print(f"{Colors.RED}❌ Неверный выбор{Colors.RESET}")
                    
            except KeyboardInterrupt:
                print(f"\n{Colors.YELLOW}👋 До свидания!{Colors.RESET}")
                break
            except EOFError:
                print(f"\n{Colors.YELLOW}👋 EOF получен, выход{Colors.RESET}")
                break
            except Exception as e:
                print(f"{Colors.RED}❌ Ошибка: {e}{Colors.RESET}")
    
    def chapter_menu(self):
        """Меню выбора главы"""
        self.show_chapters_menu()
        try:
            choice = int(input(f"\n{Colors.GREEN}Выберите главу: {Colors.RESET}"))
            if choice == 0:
                return
            elif 1 <= choice <= len(CHAPTER_TITLES):
                chapter_num = list(CHAPTER_TITLES.keys())[choice - 1]
                self.load_chapter(chapter_num)
            else:
                print(f"{Colors.RED}❌ Неверный выбор{Colors.RESET}")
        except (ValueError, EOFError):
            print(f"{Colors.RED}❌ Введите число{Colors.RESET}")
    
    def character_menu(self):
        """Меню выбора персонажа"""
        if not self.current_characters:
            print(f"{Colors.RED}❌ Сначала выберите главу{Colors.RESET}")
            return
        
        self.show_characters_menu()
        try:
            choice = int(input(f"\n{Colors.GREEN}Выберите персонажа: {Colors.RESET}"))
            if choice == 0:
                return
            elif 1 <= choice <= len(self.current_characters):
                character = self.current_characters[choice - 1]
                asyncio.run(self.chat_with_character(character))
            else:
                print(f"{Colors.RED}❌ Неверный выбор{Colors.RESET}")
        except (ValueError, EOFError):
            print(f"{Colors.RED}❌ Введите число{Colors.RESET}")
    
    def show_info(self):
        """Показать информацию о проекте"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}ℹ️  ИНФОРМАЦИЯ О ПРОЕКТЕ:{Colors.RESET}")
        print(f"{Colors.CYAN}SUPPERTIME GOSPEL THEATRE{Colors.RESET}")
        print(f"{Colors.WHITE}Интерактивный театр персонажей{Colors.RESET}")
        print(f"{Colors.YELLOW}Персонажи: {len(self.hero_manager.heroes)}{Colors.RESET}")
        print(f"{Colors.YELLOW}Главы: {len(CHAPTER_TITLES)}{Colors.RESET}")
        print(f"{Colors.GREEN}Модель: {settings.openai_model}{Colors.RESET}")
        print(f"{Colors.GREEN}Температура: {settings.openai_temperature}{Colors.RESET}")

def main():
    """Главная функция"""
    # Проверяем переменные окружения
    if not os.getenv("OPENAI_API_KEY"):
        print(f"{Colors.RED}❌ Установите OPENAI_API_KEY{Colors.RESET}")
        print(f"{Colors.YELLOW}export OPENAI_API_KEY='your-key-here'{Colors.RESET}")
        sys.exit(1)
    
    try:
        app = SuppertimeTermux()
        app.show_banner()
        app.main_menu()
    except Exception as e:
        print(f"{Colors.RED}❌ Критическая ошибка: {e}{Colors.RESET}")
        sys.exit(1)

if __name__ == "__main__":
    main()
