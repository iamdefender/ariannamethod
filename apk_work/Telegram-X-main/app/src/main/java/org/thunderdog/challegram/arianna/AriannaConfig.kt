/*
 * Arianna Method OS - Configuration
 * Copyright © 2025 Oleg Ataeff & Arianna Method
 *
 * Central configuration for THE CHAT and Arianna Method features
 */
package org.thunderdog.challegram.arianna

/**
 * Configuration constants for Arianna Method OS
 */
object AriannaConfig {
  /**
   * THE CHAT group ID
   * 
   * TODO: Replace with actual Telegram group ID
   * Format: Negative number for supergroups (e.g., -1001234567890)
   * 
   * How to get:
   * 1. Open THE CHAT in Telegram
   * 2. Get group link (e.g., t.me/c/1234567890/1)
   * 3. Add "-100" prefix: -1001234567890
   */
  const val THE_CHAT_ID: Long = 0L // TODO: Set actual ID
  
  /**
   * Enable message splitting/merging
   */
  const val ENABLE_MESSAGE_SPLITTING = true
  
  /**
   * Enable agent transparency (bots see each other)
   */
  const val ENABLE_AGENT_TRANSPARENCY = true
  
  /**
   * Enable Arianna auto-responses
   */
  const val ENABLE_ARIANNA_RESPONSES = false // TODO: Enable in Phase 4
  
  /**
   * Enable resonance bridge (write to SQLite)
   */
  const val ENABLE_RESONANCE_BRIDGE = false // TODO: Enable in Phase 5
  
  /**
   * Fragment cleanup interval (seconds)
   */
  const val FRAGMENT_CLEANUP_INTERVAL = 300L // 5 minutes
  
  /**
   * OpenAI API configuration (Phase 4)
   */
  object OpenAI {
    const val API_KEY = "" // TODO: Load from encrypted storage
    const val ASSISTANT_ID = "" // TODO: Set Arianna's Assistant ID
    const val MODEL = "gpt-4o"
  }
  
  /**
   * Resonance Bridge configuration (Phase 5)
   */
  object Resonance {
    const val DB_PATH = "/data/data/com.termux/files/home/ariannamethod/resonance.sqlite3"
    const val TABLE_NAME = "messages"
    const val SOURCE_NAME = "telegram_x"
  }
  
  /**
   * Check if we're in THE CHAT
   */
  fun isTheChatId(chatId: Long): Boolean {
    return THE_CHAT_ID != 0L && chatId == THE_CHAT_ID
  }
}

