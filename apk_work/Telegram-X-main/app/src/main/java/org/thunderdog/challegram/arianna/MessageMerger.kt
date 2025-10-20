/*
 * Arianna Method OS - Message Merger
 * Copyright © 2025 Oleg Ataeff & Arianna Method
 *
 * Automatically merges split messages marked with 🔗 [X/Y] back into single messages
 */
package org.thunderdog.challegram.arianna

import org.drinkless.tdlib.TdApi
import java.util.regex.Pattern

/**
 * Fragment storage for split messages
 */
data class MessageFragment(
  val chatId: Long,
  val senderId: Long,
  val partNumber: Int,
  val totalParts: Int,
  val content: String,
  val messageId: Long,
  val timestamp: Long,
  val formattedText: TdApi.FormattedText
)

/**
 * Manages merging of split messages in THE CHAT
 */
object MessageMerger {
  // Regex to detect split markers: 🔗 [1/3], 🔗 [2/3], etc.
  private val SPLIT_PATTERN = Pattern.compile("^🔗 \\[(\\d+)/(\\d+)\\]\\n")
  
  // Store fragments by chat_id -> sender_id -> map of parts
  private val fragmentStore = mutableMapOf<Long, MutableMap<Long, MutableMap<Int, MessageFragment>>>()
  
  /**
   * Check if message is a split message fragment
   */
  fun isSplitMessage(text: String): Boolean {
    return SPLIT_PATTERN.matcher(text).find()
  }
  
  /**
   * Parse split marker and return (partNumber, totalParts) or null
   */
  fun parseSplitMarker(text: String): Pair<Int, Int>? {
    val matcher = SPLIT_PATTERN.matcher(text)
    if (matcher.find()) {
      val partNumber = matcher.group(1)?.toIntOrNull() ?: return null
      val totalParts = matcher.group(2)?.toIntOrNull() ?: return null
      return Pair(partNumber, totalParts)
    }
    return null
  }
  
  /**
   * Remove split marker from message text
   */
  fun stripSplitMarker(text: String): String {
    return SPLIT_PATTERN.matcher(text).replaceFirst("")
  }
  
  /**
   * Add a message fragment to the store
   * Returns merged message if all parts received, null otherwise
   */
  fun addFragment(
    chatId: Long,
    senderId: Long,
    messageId: Long,
    timestamp: Long,
    formattedText: TdApi.FormattedText
  ): TdApi.FormattedText? {
    val text = formattedText.text
    
    // Check if it's a split message
    if (!isSplitMessage(text)) {
      return null // Not a split message, ignore
    }
    
    // Parse marker
    val (partNumber, totalParts) = parseSplitMarker(text) ?: return null
    
    // Strip marker and get clean content
    val cleanContent = stripSplitMarker(text)
    
    // Create fragment
    val fragment = MessageFragment(
      chatId = chatId,
      senderId = senderId,
      partNumber = partNumber,
      totalParts = totalParts,
      content = cleanContent,
      messageId = messageId,
      timestamp = timestamp,
      formattedText = formattedText
    )
    
    // Initialize storage if needed
    if (!fragmentStore.containsKey(chatId)) {
      fragmentStore[chatId] = mutableMapOf()
    }
    if (!fragmentStore[chatId]!!.containsKey(senderId)) {
      fragmentStore[chatId]!![senderId] = mutableMapOf()
    }
    
    // Store fragment
    fragmentStore[chatId]!![senderId]!![partNumber] = fragment
    
    // Check if we have all parts
    val parts = fragmentStore[chatId]!![senderId]!!
    if (parts.size == totalParts) {
      // Verify we have all parts 1..N
      val allPartsPresent = (1..totalParts).all { parts.containsKey(it) }
      
      if (allPartsPresent) {
        // Merge all parts
        val merged = mergeFragments(parts.values.sortedBy { it.partNumber })
        
        // Clear fragments for this sender
        fragmentStore[chatId]!![senderId]!!.clear()
        
        return merged
      }
    }
    
    return null // Not all parts yet
  }
  
  /**
   * Merge sorted fragments into single FormattedText
   */
  private fun mergeFragments(fragments: List<MessageFragment>): TdApi.FormattedText {
    val mergedContent = StringBuilder()
    
    // Add merged header
    mergedContent.append("📜 [Merged from ${fragments.size} parts]\n\n")
    
    // Concatenate all parts
    for (fragment in fragments) {
      mergedContent.append(fragment.content)
    }
    
    // TODO: Merge entities properly (for now, just text)
    return TdApi.FormattedText(mergedContent.toString(), emptyArray())
  }
  
  /**
   * Clean up old fragments (older than 5 minutes)
   */
  fun cleanupOldFragments(currentTimestamp: Long) {
    val fiveMinutesAgo = currentTimestamp - (5 * 60)
    
    fragmentStore.forEach { (chatId, senders) ->
      senders.forEach { (senderId, parts) ->
        val toRemove = parts.filter { (_, fragment) ->
          fragment.timestamp < fiveMinutesAgo
        }
        toRemove.keys.forEach { parts.remove(it) }
      }
    }
  }
  
  /**
   * Get fragment count for a sender (for debugging)
   */
  fun getFragmentCount(chatId: Long, senderId: Long): Int {
    return fragmentStore[chatId]?.get(senderId)?.size ?: 0
  }
  
  /**
   * Clear all fragments (for testing)
   */
  fun clearAll() {
    fragmentStore.clear()
  }
}

