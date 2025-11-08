package com.ariannamethod.molly

import android.app.Activity
import android.appwidget.AppWidgetManager
import android.content.Intent
import android.os.Bundle
import android.view.Gravity
import android.view.ViewGroup
import android.view.inputmethod.EditorInfo
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.TextView

/**
 * Configuration activity for user input
 * Opened when user taps the widget
 */
class MollyConfigActivity : Activity() {
    
    private var appWidgetId = AppWidgetManager.INVALID_APPWIDGET_ID
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        // Get widget ID
        appWidgetId = intent.getIntExtra(
            AppWidgetManager.EXTRA_APPWIDGET_ID,
            AppWidgetManager.INVALID_APPWIDGET_ID
        )
        
        // Setup minimal UI
        val layout = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(32, 32, 32, 32)
            setBackgroundColor(0xFFFFFFFF.toInt())
        }
        
        // Title
        val title = TextView(this).apply {
            text = "Say something to Molly..."
            textSize = 16f
            setTextColor(0xFF000000.toInt())
            gravity = Gravity.CENTER
            setPadding(0, 0, 0, 24)
        }
        layout.addView(title)
        
        // Input field
        val input = EditText(this).apply {
            hint = "say something..."
            textSize = 14f
            setTextColor(0xFF000000.toInt())
            setHintTextColor(0xFF888888.toInt())
            maxLines = 3
            imeOptions = EditorInfo.IME_ACTION_SEND
            
            val params = LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT
            )
            layoutParams = params
        }
        
        input.setOnEditorActionListener { v, actionId, _ ->
            if (actionId == EditorInfo.IME_ACTION_SEND) {
                val userText = v.text.toString().take(100) // Limit to 100 chars
                if (userText.isNotBlank()) {
                    submitInput(userText)
                }
                true
            } else {
                false
            }
        }
        
        layout.addView(input)
        
        // Instruction text
        val instruction = TextView(this).apply {
            text = "Press Enter to send (max 100 chars)"
            textSize = 12f
            setTextColor(0xFF666666.toInt())
            gravity = Gravity.CENTER
            setPadding(0, 16, 0, 0)
        }
        layout.addView(instruction)
        
        setContentView(layout)
        
        // Focus input
        input.requestFocus()
    }
    
    private fun submitInput(text: String) {
        // Send broadcast to widget with user input
        val intent = Intent(this, MollyWidget::class.java).apply {
            action = "com.ariannamethod.molly.ACTION_SUBMIT"
            putExtra("user_input", text)
        }
        sendBroadcast(intent)
        
        // Set result and finish
        val resultValue = Intent().apply {
            putExtra(AppWidgetManager.EXTRA_APPWIDGET_ID, appWidgetId)
        }
        setResult(RESULT_OK, resultValue)
        finish()
    }
    
    override fun onBackPressed() {
        // Cancel configuration
        setResult(RESULT_CANCELED)
        super.onBackPressed()
    }
}
