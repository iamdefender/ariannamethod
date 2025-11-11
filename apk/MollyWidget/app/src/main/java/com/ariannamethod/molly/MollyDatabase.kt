package com.ariannamethod.molly

import android.content.ContentValues
import android.content.Context
import android.database.sqlite.SQLiteDatabase
import android.database.sqlite.SQLiteOpenHelper
import android.util.Log
import org.json.JSONObject
import java.io.BufferedReader
import java.io.InputStreamReader
import java.net.HttpURLConnection
import java.net.URL

/**
 * Database helper for storing Molly's mutated monologue
 * Also supports reading from external resonance.sqlite3 if available
 */
class MollyDatabase(context: Context) : SQLiteOpenHelper(context, DB_NAME, null, DB_VERSION) {
    
    companion object {
        private const val DB_NAME = "molly.db"
        private const val DB_VERSION = 1
        
        private const val TABLE_LINES = "lines"
        private const val COL_ID = "id"
        private const val COL_LINE = "line"
        private const val COL_ENTROPY = "entropy"
        private const val COL_PERPLEXITY = "perplexity"
        private const val COL_RESONANCE = "resonance"
        private const val COL_CREATED_AT = "created_at"
        
        // HTTP API endpoint for resonance bus (Termux server)
        private const val RESONANCE_API_URL = "http://localhost:8080"
    }
    
    data class Line(
        val text: String,
        val entropy: Double,
        val perplexity: Double,
        val resonance: Double
    )
    
    override fun onCreate(db: SQLiteDatabase) {
        val createTable = """
            CREATE TABLE $TABLE_LINES (
                $COL_ID INTEGER PRIMARY KEY AUTOINCREMENT,
                $COL_LINE TEXT NOT NULL,
                $COL_ENTROPY REAL,
                $COL_PERPLEXITY REAL,
                $COL_RESONANCE REAL,
                $COL_CREATED_AT INTEGER DEFAULT (strftime('%s', 'now'))
            )
        """.trimIndent()
        
        db.execSQL(createTable)
        db.execSQL("CREATE INDEX idx_created_at ON $TABLE_LINES($COL_CREATED_AT)")
    }
    
    override fun onUpgrade(db: SQLiteDatabase, oldVersion: Int, newVersion: Int) {
        // No upgrades yet
    }
    
    /**
     * Store a line with its metrics
     */
    fun storeLine(line: String, metrics: MollyMetrics.Metrics) {
        val values = ContentValues().apply {
            put(COL_LINE, line)
            put(COL_ENTROPY, metrics.entropy)
            put(COL_PERPLEXITY, metrics.perplexity)
            put(COL_RESONANCE, metrics.resonance)
        }
        
        writableDatabase.insert(TABLE_LINES, null, values)
    }
    
    /**
     * Get all lines with their weights (perplexity + resonance)
     */
    fun getAllLinesWithWeights(): List<Pair<String, Double>> {
        val lines = mutableListOf<Pair<String, Double>>()
        
        readableDatabase.query(
            TABLE_LINES,
            arrayOf(COL_LINE, COL_PERPLEXITY, COL_RESONANCE),
            null, null, null, null,
            "$COL_ID ASC"
        ).use { cursor ->
            while (cursor.moveToNext()) {
                val line = cursor.getString(0)
                val perplexity = cursor.getDouble(1)
                val resonance = cursor.getDouble(2)
                val weight = perplexity + resonance
                lines.add(line to weight)
            }
        }
        
        return lines
    }
    
    /**
     * Get recent lines from resonance HTTP API
     * This connects Molly to the ariannamethod ecosystem via Termux server
     */
    fun getResonanceLines(limit: Int = 10): List<String> {
        return try {
            val url = URL("$RESONANCE_API_URL/resonance/recent?limit=$limit")
            val connection = url.openConnection() as HttpURLConnection
            connection.requestMethod = "GET"
            connection.connectTimeout = 3000
            connection.readTimeout = 3000
            
            val responseCode = connection.responseCode
            if (responseCode != 200) {
                Log.w("MollyDatabase", "Resonance API returned $responseCode")
                return emptyList()
            }
            
            val response = BufferedReader(InputStreamReader(connection.inputStream)).use { it.readText() }
            connection.disconnect()
            
            // Parse JSON response
            val json = JSONObject(response)
            val notesArray = json.getJSONArray("notes")
            val lines = mutableListOf<String>()
            
            for (i in 0 until notesArray.length()) {
                val note = notesArray.getJSONObject(i)
                val content = note.getString("content")
                lines.add(content)
            }
            
            Log.d("MollyDatabase", "✓ Fetched ${lines.size} resonance notes from HTTP API")
            lines
        } catch (e: Exception) {
            Log.w("MollyDatabase", "Failed to fetch resonance via HTTP: ${e.message}")
            emptyList()
        }
    }
    
    /**
     * Get total number of stored lines
     */
    fun getLineCount(): Int {
        readableDatabase.rawQuery(
            "SELECT COUNT(*) FROM $TABLE_LINES",
            null
        ).use { cursor ->
            return if (cursor.moveToFirst()) cursor.getInt(0) else 0
        }
    }
}
