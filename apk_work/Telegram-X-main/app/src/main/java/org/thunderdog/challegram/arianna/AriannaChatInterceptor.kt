/*
 * Arianna Method OS - Chat Interceptor
 * Copyright © 2025 Oleg Ataeff & Arianna Method
 *
 * Intercepts messages in THE CHAT for merging and processing
 */
package org.thunderdog.challegram.arianna

import org.drinkless.tdlib.TdApi
import org.thunderdog.challegram.telegram.MessageListener
import org.thunderdog.challegram.telegram.Tdlib
import android.util.Log

/**
 * Intercepts all messages in THE CHAT for:
 * 1. Merging split messages
 * 2. Writing to resonance.sqlite3
 * 3. Triggering Arianna responses
 */
class AriannaChatInterceptor(
  private val tdlib: Tdlib,
  private val theChatId: Long
) : MessageListener {
  
  companion object {
    private const val TAG = "AriannaChatInterceptor"
  }
  
  /**
   * Called when a new message arrives
   */
  override fun onNewMessage(message: TdApi.Message) {
    // Only process messages from THE CHAT
    if (message.chatId != theChatId) {
      return
    }
    
    // Only process text messages
    if (message.content.constructor != TdApi.MessageText.CONSTRUCTOR) {
      return
    }
    
    val textContent = message.content as TdApi.MessageText
    val text = textContent.text.text
    
    Log.d(TAG, "New message in THE CHAT: ${text.take(100)}...")
    
    // Check if it's a split message
    if (MessageMerger.isSplitMessage(text)) {
      handleSplitMessage(message, textContent.text)
    } else {
      // Regular message, process normally
      handleRegularMessage(message, text)
    }
  }
  
  /**
   * Handle split message fragment
   */
  private fun handleSplitMessage(message: TdApi.Message, formattedText: TdApi.FormattedText) {
    val senderId = getSenderId(message)
    
    Log.d(TAG, "Split message fragment detected from sender $senderId")
    
    // Try to merge
    val merged = MessageMerger.addFragment(
      chatId = message.chatId,
      senderId = senderId,
      messageId = message.id,
      timestamp = message.date.toLong(),
      formattedText = formattedText
    )
    
    if (merged != null) {
      Log.d(TAG, "All fragments received! Merged message length: ${merged.text.length}")
      
      // TODO: Display merged message in UI
      // TODO: Hide individual fragments
      
      // Process the complete merged message
      handleRegularMessage(message, merged.text)
    } else {
      val fragmentCount = MessageMerger.getFragmentCount(message.chatId, senderId)
      Log.d(TAG, "Waiting for more fragments... ($fragmentCount received so far)")
      
      // TODO: Show "Loading..." indicator in UI
    }
  }
  
  /**
   * Handle regular (non-split) message
   */
  private fun handleRegularMessage(message: TdApi.Message, text: String) {
    Log.d(TAG, "Processing regular message: ${text.take(50)}...")
    
    // TODO Phase 5: Write to resonance.sqlite3
    // writeToResonance(message, text)
    
    // TODO Phase 4: Check if Arianna should respond
    // if (shouldAriannaRespond(text)) {
    //   AriannaCore.processMessage(message)
    // }
  }
  
  /**
   * Get sender ID from message
   */
  private fun getSenderId(message: TdApi.Message): Long {
    return when (val sender = message.senderId) {
      is TdApi.MessageSenderUser -> sender.userId
      is TdApi.MessageSenderChat -> sender.chatId
      else -> 0L
    }
  }
  
  /**
   * Cleanup old fragments periodically
   */
  fun cleanup() {
    val currentTime = System.currentTimeMillis() / 1000
    MessageMerger.cleanupOldFragments(currentTime)
  }
}

