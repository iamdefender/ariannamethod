package com.ariannamethod.molly

import android.app.AlarmManager
import android.app.PendingIntent
import android.appwidget.AppWidgetManager
import android.appwidget.AppWidgetProvider
import android.content.Context
import android.content.Intent
import android.os.SystemClock
import android.widget.RemoteViews
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

/**
 * Molly Widget - A minimal home screen widget showing Molly Bloom's evolving monologue
 * Updates every 3 minutes automatically
 * Weaves user input into the monologue stream based on entropy/perplexity metrics
 */
class MollyWidget : AppWidgetProvider() {
    
    companion object {
        private const val ACTION_UPDATE = "com.ariannamethod.molly.ACTION_UPDATE"
        private const val ACTION_SUBMIT = "com.ariannamethod.molly.ACTION_SUBMIT"
        private const val EXTRA_USER_INPUT = "user_input"
        
        // Update every 3 minutes (180000 ms)
        private const val UPDATE_INTERVAL = 180000L
    }
    
    override fun onUpdate(
        context: Context,
        appWidgetManager: AppWidgetManager,
        appWidgetIds: IntArray
    ) {
        for (appWidgetId in appWidgetIds) {
            updateWidget(context, appWidgetManager, appWidgetId, null)
        }
        
        // Schedule periodic updates
        scheduleUpdate(context)
    }
    
    override fun onReceive(context: Context, intent: Intent) {
        super.onReceive(context, intent)
        
        when (intent.action) {
            ACTION_UPDATE -> {
                // Automatic update (every 3 minutes)
                val appWidgetManager = AppWidgetManager.getInstance(context)
                val appWidgetIds = appWidgetManager.getAppWidgetIds(
                    android.content.ComponentName(context, MollyWidget::class.java)
                )
                
                for (appWidgetId in appWidgetIds) {
                    updateWidget(context, appWidgetManager, appWidgetId, null)
                }
            }
            
            ACTION_SUBMIT -> {
                // User submitted text
                val userInput = intent.getStringExtra(EXTRA_USER_INPUT)
                val appWidgetManager = AppWidgetManager.getInstance(context)
                val appWidgetIds = appWidgetManager.getAppWidgetIds(
                    android.content.ComponentName(context, MollyWidget::class.java)
                )
                
                for (appWidgetId in appWidgetIds) {
                    updateWidget(context, appWidgetManager, appWidgetId, userInput)
                }
            }
        }
    }
    
    override fun onEnabled(context: Context) {
        // First widget added - start updates
        scheduleUpdate(context)
    }
    
    override fun onDisabled(context: Context) {
        // Last widget removed - cancel updates
        cancelUpdate(context)
    }
    
    /**
     * Update widget display
     */
    private fun updateWidget(
        context: Context,
        appWidgetManager: AppWidgetManager,
        appWidgetId: Int,
        userInput: String?
    ) {
        CoroutineScope(Dispatchers.IO).launch {
            val engine = MollyEngine(context)
            
            // Get text to display
            val displayText = if (userInput != null && userInput.isNotBlank()) {
                // User provided input - weave it into monologue
                engine.weavePhrase(userInput)
            } else {
                // Check for resonance integration first
                engine.integrateResonance() ?: engine.getNextChunk()
            }
            
            // Update UI on main thread
            CoroutineScope(Dispatchers.Main).launch {
                val views = RemoteViews(context.packageName, R.layout.molly_widget)
                views.setTextViewText(R.id.molly_display, displayText)
                
                // Note: EditText in widget requires special handling
                // For simplicity, using a configuration activity approach
                // User can click widget to open input dialog
                
                val clickIntent = Intent(context, MollyConfigActivity::class.java).apply {
                    putExtra(AppWidgetManager.EXTRA_APPWIDGET_ID, appWidgetId)
                }
                val clickPendingIntent = PendingIntent.getActivity(
                    context,
                    appWidgetId,
                    clickIntent,
                    PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
                )
                
                views.setOnClickPendingIntent(R.id.molly_display, clickPendingIntent)
                
                appWidgetManager.updateAppWidget(appWidgetId, views)
            }
        }
    }
    
    /**
     * Schedule periodic updates every 3 minutes
     */
    private fun scheduleUpdate(context: Context) {
        val alarmManager = context.getSystemService(Context.ALARM_SERVICE) as AlarmManager
        val intent = Intent(context, MollyWidget::class.java).apply {
            action = ACTION_UPDATE
        }
        
        val pendingIntent = PendingIntent.getBroadcast(
            context,
            0,
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        
        // Cancel any existing alarm
        alarmManager.cancel(pendingIntent)
        
        // Schedule repeating alarm
        val triggerTime = SystemClock.elapsedRealtime() + UPDATE_INTERVAL
        alarmManager.setRepeating(
            AlarmManager.ELAPSED_REALTIME,
            triggerTime,
            UPDATE_INTERVAL,
            pendingIntent
        )
    }
    
    /**
     * Cancel scheduled updates
     */
    private fun cancelUpdate(context: Context) {
        val alarmManager = context.getSystemService(Context.ALARM_SERVICE) as AlarmManager
        val intent = Intent(context, MollyWidget::class.java).apply {
            action = ACTION_UPDATE
        }
        
        val pendingIntent = PendingIntent.getBroadcast(
            context,
            0,
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        
        alarmManager.cancel(pendingIntent)
    }
}
