package com.ariannamethod.molly

import android.content.ContentValues
import android.content.Context
import android.database.sqlite.SQLiteDatabase
import android.database.sqlite.SQLiteOpenHelper
import java.io.File

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
        
        // Path to shared resonance database (ariannamethod ecosystem)
        private const val RESONANCE_DB_PATH = "/sdcard/ariannamethod/resonance.sqlite3"
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
     * Get recent lines from resonance.sqlite3 if available
     * This connects Molly to the ariannamethod ecosystem
     */
    fun getResonanceLines(limit: Int = 10): List<String> {
        val resonanceFile = File(RESONANCE_DB_PATH)
        if (!resonanceFile.exists()) return emptyList()
        
        return try {
            val db = SQLiteDatabase.openDatabase(
                resonanceFile.path,
                null,
                SQLiteDatabase.OPEN_READONLY
            )
            
            val lines = mutableListOf<String>()
            db.rawQuery(
                "SELECT content FROM events ORDER BY timestamp DESC LIMIT ?",
                arrayOf(limit.toString())
            ).use { cursor ->
                while (cursor.moveToNext()) {
                    lines.add(cursor.getString(0))
                }
            }
            
            db.close()
            lines
        } catch (e: Exception) {
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
