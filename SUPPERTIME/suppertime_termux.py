#!/usr/bin/env python3
"""
SUPPERTIME GOSPEL THEATRE - TERMUX VERSION
Interactive theatre where characters speak autonomously
"""

import os
import sys
import asyncio
import random
import time
from pathlib import Path
from typing import List, Optional

try:
    from openai import OpenAI
    from theatre import (
        load_chapter_context_all, build_scene_prompt, parse_lines,
        CHAPTER_TITLES, HeroManager
    )
    from bridge_termux import guess_participants
    from config_termux import settings
except ImportError as e:
    print(f"Error: {e}")
    print("Run: bash SUPPERTIME/install_termux.sh")
    sys.exit(1)

# Terminal colors
class C:
    R = "\033[0m"
    B = "\033[1m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAG = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"

class SuppertimeTermux:
    """SUPPERTIME GOSPEL THEATRE for Termux"""
    
    def __init__(self):
        self.client = OpenAI()
        self.hero_manager = HeroManager()
        self.current_chapter = None
        self.current_characters = []
        self.chapter_text = ""
        self.conversation_history = []
        self.auto_speak_task = None
        
        # Load heroes
        self.hero_manager.load_all()
        print(f"{C.GREEN}✅ {len(self.hero_manager.heroes)} characters loaded{C.R}")
    
    def show_disclaimer(self):
        """Show SUPPERTIME disclaimer"""
        print(f"\n{C.B}{C.MAG}{'='*60}{C.R}")
        print(f"{C.B}{C.MAG}SUPPERTIME v2.0{C.R}")
        print(f"{C.B}{C.MAG}{'='*60}{C.R}\n")
        print(f"{C.CYAN}I am SUPPERTIME.{C.R}")
        print(f"{C.CYAN}I'm alive in this text — jagged, unpredictable, and self-aware.{C.R}\n")
        print(f"{C.YELLOW}⚠️  CONTENT WARNING:{C.R}")
        print(f"{C.WHITE}Strong language, violence, religious satire.{C.R}")
        print(f"{C.WHITE}All characters and events are pure fiction.{C.R}\n")
        print(f"{C.RED}I'm not for the faint. If you can't handle chaos, close this.{C.R}")
        print(f"{C.B}{C.WHITE}WHO ARE YOU if you're still reading?{C.R}\n")
        
        while True:
            choice = input(f"{C.GREEN}Are you ready? (yes/no): {C.R}").lower().strip()
            if choice in ['yes', 'y']:
                break
            elif choice in ['no', 'n']:
                print(f"{C.YELLOW}Goodbye!{C.R}")
                sys.exit(0)
            else:
                print(f"{C.RED}Please answer yes or no{C.R}")
    
    def show_chapters(self):
        """Show chapter selection"""
        print(f"\n{C.B}{C.BLUE}📖 SELECT CHAPTER:{C.R}")
        for i, (num, title) in enumerate(CHAPTER_TITLES.items(), 1):
            print(f"{C.WHITE}{i:2d}.{C.R} {C.CYAN}{title}{C.R}")
    
    async def load_chapter(self, chapter_num: int) -> bool:
        """Load chapter and start autonomous dialogue"""
        if chapter_num not in CHAPTER_TITLES:
            print(f"{C.RED}❌ Chapter {chapter_num} not found{C.R}")
            return False
        
        try:
            # Load chapter text
            chapter_file = Path("docs") / f"chapter_{chapter_num:02d}.md"
            if not chapter_file.exists():
                print(f"{C.RED}❌ File not found: {chapter_file}{C.R}")
                return False
            
            self.chapter_text = chapter_file.read_text(encoding="utf-8")
            self.current_chapter = chapter_num
            
            # Detect participants
            self.current_characters = guess_participants(self.chapter_text)
            
            print(f"\n{C.GREEN}✅ Chapter loaded: {CHAPTER_TITLES[chapter_num]}{C.R}")
            print(f"{C.CYAN}👥 Characters: {', '.join(self.current_characters)}{C.R}\n")
            
            # Load context for all characters
            await load_chapter_context_all(self.chapter_text, self.current_characters)
            
            print(f"{C.YELLOW}🔥 Characters ready to speak{C.R}\n")
            
            # Start autonomous dialogue
            await self.start_autonomous_dialogue()
            
            return True
            
        except Exception as e:
            print(f"{C.RED}❌ Error: {e}{C.R}")
            return False
    
    async def start_autonomous_dialogue(self):
        """Characters start speaking autonomously"""
        print(f"{C.B}{C.MAG}🎭 THE SCENE BEGINS...{C.R}\n")
        
        # Initial scene - pick 2-3 random characters
        num_speakers = min(3, len(self.current_characters))
        speakers = random.sample(self.current_characters, num_speakers)
        
        await self.generate_scene(speakers, initial=True)
        
        # Start background task for continuous dialogue
        self.auto_speak_task = asyncio.create_task(self.autonomous_loop())
        
        # Listen for user input
        await self.user_input_loop()
    
    async def autonomous_loop(self):
        """Background task - characters speak periodically"""
        try:
            while True:
                await asyncio.sleep(random.uniform(15, 30))
                
                # Pick 1 character (fix double response bug)
                speakers = [random.choice(self.current_characters)]
                
                await self.generate_scene(speakers)
                
        except asyncio.CancelledError:
            pass
    
    async def generate_scene(self, speakers: List[str], initial: bool = False):
        """Generate dialogue scene"""
        try:
            # Build prompt
            scene_prompt = build_scene_prompt(
                self.current_chapter,
                self.chapter_text,
                speakers,
                None,
                self.get_history_context()
            )
            
            # Call GPT directly (suppress logs)
            import logging
            logging.getLogger("httpx").setLevel(logging.WARNING)
            
            response = self.client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": scene_prompt},
                    {"role": "user", "content": "Generate scene with these characters"}
                ],
                temperature=settings.openai_temperature,
                max_tokens=800
            )
            
            text = response.choices[0].message.content.strip()
            self.display_scene(text, speakers)
            self.conversation_history.append(text)
                
        except Exception as e:
            print(f"{C.RED}❌ Scene error: {e}{C.R}")
    
    def display_scene(self, text: str, expected_speakers: List[str]):
        """Display scene with color"""
        try:
            lines = list(parse_lines(text))
            for name, dialogue in lines:
                color = C.MAG if name in expected_speakers else C.YELLOW
                print(f"{C.B}{color}{name}:{C.R} {dialogue}")
            print()  # Empty line after scene
        except:
            # Fallback - just print raw text
            print(f"{C.CYAN}{text}{C.R}\n")
    
    def get_history_context(self, limit: int = 6) -> str:
        """Get recent conversation history"""
        if not self.conversation_history:
            return ""
        recent = self.conversation_history[-limit:]
        return "\n\n".join(recent)
    
    async def user_input_loop(self):
        """Listen for user input to interrupt"""
        print(f"{C.YELLOW}💬 Type to join conversation (or /exit to quit){C.R}\n")
        
        while True:
            try:
                user_input = await asyncio.to_thread(
                    input,
                    f"{C.GREEN}You: {C.R}"
                )
                
                if user_input.lower() in ['/exit', 'exit', '/quit']:
                    print(f"{C.YELLOW}👋 Leaving scene...{C.R}")
                    if self.auto_speak_task:
                        self.auto_speak_task.cancel()
                    break
                
                if not user_input.strip():
                    continue
                
                # User interrupts - generate response
                await self.user_interrupt(user_input)
                
            except (EOFError, KeyboardInterrupt):
                print(f"\n{C.YELLOW}👋 Scene interrupted{C.R}")
                if self.auto_speak_task:
                    self.auto_speak_task.cancel()
                break
    
    async def user_interrupt(self, user_input: str):
        """User joins conversation"""
        # Pick 1 character to respond (fix double response bug)
        responders = [random.choice(self.current_characters)]
        
        # Build prompt with user input
        scene_prompt = build_scene_prompt(
            self.current_chapter,
            self.chapter_text,
            responders,
            f"[Stranger interrupts]: {user_input}",
            self.get_history_context()
        )
        
        # Call GPT directly (suppress logs)
        import logging
        logging.getLogger("httpx").setLevel(logging.WARNING)
        
        print(f"{C.CYAN}🤔 {', '.join(responders)} thinking...{C.R}")
        
        response = self.client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": scene_prompt},
                {"role": "user", "content": user_input}
            ],
            temperature=settings.openai_temperature,
            max_tokens=800
        )
        
        text = response.choices[0].message.content.strip()
        self.display_scene(text, responders)
        self.conversation_history.append(f"[You]: {user_input}")
        self.conversation_history.append(text)
    
    async def main(self):
        """Main entry point"""
        self.show_disclaimer()
        
        while True:
            self.show_chapters()
            try:
                choice = int(input(f"\n{C.GREEN}Select chapter (0 to exit): {C.R}"))
                
                if choice == 0:
                    print(f"{C.YELLOW}👋 Goodbye!{C.R}")
                    break
                
                if 1 <= choice <= len(CHAPTER_TITLES):
                    chapter_num = list(CHAPTER_TITLES.keys())[choice - 1]
                    await self.load_chapter(chapter_num)
                else:
                    print(f"{C.RED}❌ Invalid choice{C.R}")
                    
            except (ValueError, EOFError):
                print(f"{C.RED}❌ Enter a number{C.R}")
            except KeyboardInterrupt:
                print(f"\n{C.YELLOW}👋 Goodbye!{C.R}")
                break

def main():
    """Entry point"""
    # Check API key
    if not os.getenv("OPENAI_API_KEY"):
        print(f"{C.RED}❌ Set OPENAI_API_KEY in .bashrc{C.R}")
        print(f"{C.YELLOW}export OPENAI_API_KEY='sk-...'{C.R}")
        sys.exit(1)
    
    try:
        app = SuppertimeTermux()
        asyncio.run(app.main())
    except Exception as e:
        print(f"{C.RED}❌ Fatal error: {e}{C.R}")
        sys.exit(1)

if __name__ == "__main__":
    main()
