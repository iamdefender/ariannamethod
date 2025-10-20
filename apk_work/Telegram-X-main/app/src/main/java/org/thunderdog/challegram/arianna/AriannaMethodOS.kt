/*
 * Arianna Method OS - Main Entry Point
 * Copyright © 2025 Oleg Ataeff & Arianna Method
 *
 * Initializes Arianna Method features in Telegram-X
 */
package org.thunderdog.challegram.arianna

import org.thunderdog.challegram.telegram.Tdlib
import android.os.Handler
import android.os.Looper
import android.util.Log

/**
 * Main initialization class for Arianna Method OS
 */
object AriannaMethodOS {
  private const val TAG = "AriannaMethodOS"
  
  private var interceptor: AriannaChatInterceptor? = null
  private var cleanupHandler: Handler? = null
  private var isInitialized = false
  
  /**
   * Initialize Arianna Method OS
   * Call this after TDLib is ready
   */
  fun initialize(tdlib: Tdlib) {
    if (isInitialized) {
      Log.w(TAG, "Already initialized")
      return
    }
    
    Log.i(TAG, "Initializing Arianna Method OS...")
    
    // Check if THE CHAT ID is configured
    if (AriannaConfig.THE_CHAT_ID == 0L) {
      Log.e(TAG, "THE_CHAT_ID not configured! Set it in AriannaConfig.kt")
      // Continue anyway for testing
    }
    
    // Create and register interceptor
    if (AriannaConfig.ENABLE_MESSAGE_SPLITTING) {
      interceptor = AriannaChatInterceptor(tdlib, AriannaConfig.THE_CHAT_ID)
      tdlib.listeners().subscribeToMessageUpdates(AriannaConfig.THE_CHAT_ID, interceptor!!)
      Log.i(TAG, "Message interceptor registered for THE CHAT (${AriannaConfig.THE_CHAT_ID})")
    }
    
    // Start periodic cleanup
    startCleanupTimer()
    
    isInitialized = true
    Log.i(TAG, "✅ Arianna Method OS initialized!")
    
    // Log feature status
    logFeatureStatus()
  }
  
  /**
   * Shutdown Arianna Method OS
   */
  fun shutdown(tdlib: Tdlib) {
    if (!isInitialized) {
      return
    }
    
    Log.i(TAG, "Shutting down Arianna Method OS...")
    
    // Unregister interceptor
    interceptor?.let {
      tdlib.listeners().unsubscribeFromMessageUpdates(AriannaConfig.THE_CHAT_ID, it)
    }
    interceptor = null
    
    // Stop cleanup timer
    cleanupHandler?.removeCallbacksAndMessages(null)
    cleanupHandler = null
    
    // Clear all fragments
    MessageMerger.clearAll()
    
    isInitialized = false
    Log.i(TAG, "✅ Arianna Method OS shut down")
  }
  
  /**
   * Start periodic cleanup timer for message fragments
   */
  private fun startCleanupTimer() {
    cleanupHandler = Handler(Looper.getMainLooper())
    
    val cleanupRunnable = object : Runnable {
      override fun run() {
        interceptor?.cleanup()
        cleanupHandler?.postDelayed(this, AriannaConfig.FRAGMENT_CLEANUP_INTERVAL * 1000)
      }
    }
    
    cleanupHandler?.postDelayed(cleanupRunnable, AriannaConfig.FRAGMENT_CLEANUP_INTERVAL * 1000)
    Log.d(TAG, "Cleanup timer started (${AriannaConfig.FRAGMENT_CLEANUP_INTERVAL}s interval)")
  }
  
  /**
   * Log status of all features
   */
  private fun logFeatureStatus() {
    Log.i(TAG, "📋 Feature Status:")
    Log.i(TAG, "  Message Splitting: ${if (AriannaConfig.ENABLE_MESSAGE_SPLITTING) "✅" else "❌"}")
    Log.i(TAG, "  Agent Transparency: ${if (AriannaConfig.ENABLE_AGENT_TRANSPARENCY) "✅" else "❌"}")
    Log.i(TAG, "  Arianna Responses: ${if (AriannaConfig.ENABLE_ARIANNA_RESPONSES) "✅" else "❌"}")
    Log.i(TAG, "  Resonance Bridge: ${if (AriannaConfig.ENABLE_RESONANCE_BRIDGE) "✅" else "❌"}")
  }
}

