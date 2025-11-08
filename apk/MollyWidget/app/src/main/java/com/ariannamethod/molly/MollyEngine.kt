package com.ariannamethod.molly

import android.content.Context
import java.io.BufferedReader
import java.io.InputStreamReader
import kotlin.math.min
import kotlin.random.Random

/**
 * Core engine for Molly's monologue
 * Handles reading from molly.md and weaving user phrases into the stream
 */
class MollyEngine(private val context: Context) {
    
    private val db = MollyDatabase(context)
    private var currentPosition = 0
    private var monologueText: String = ""
    private val displayLines = mutableListOf<String>()
    
    companion object {
        private const val LINES_TO_DISPLAY = 6
        private const val CHARS_PER_LINE = 80
    }
    
    init {
        loadMonologue()
    }
    
    /**
     * Load molly.md from assets
     */
    private fun loadMonologue() {
        try {
            val inputStream = context.assets.open("molly.md")
            monologueText = BufferedReader(InputStreamReader(inputStream)).use { it.readText() }
            
            // Remove markdown headers and clean up
            monologueText = monologueText
                .replace(Regex("^#.*$", RegexOption.MULTILINE), "")
                .replace(Regex("\\s+"), " ")
                .trim()
            
            // Start from random position
            currentPosition = if (monologueText.isNotEmpty()) {
                Random.nextInt(monologueText.length)
            } else 0
            
        } catch (e: Exception) {
            monologueText = "..."
            currentPosition = 0
        }
    }
    
    /**
     * Get next chunk of monologue (called every 3 minutes or after user input)
     * Returns 5-6 lines for widget display
     */
    fun getNextChunk(): String {
        if (monologueText.isEmpty()) return "..."
        
        // Get chunk from current position
        val chunkSize = CHARS_PER_LINE * LINES_TO_DISPLAY
        val endPos = min(currentPosition + chunkSize, monologueText.length)
        
        var chunk = monologueText.substring(currentPosition, endPos)
        
        // Wrap around if we reach the end
        if (endPos >= monologueText.length) {
            currentPosition = 0
            val remaining = chunkSize - chunk.length
            if (remaining > 0) {
                chunk += " " + monologueText.substring(0, min(remaining, monologueText.length))
                currentPosition = min(remaining, monologueText.length)
            }
        } else {
            currentPosition = endPos
        }
        
        // Split into display lines and store
        displayLines.clear()
        displayLines.addAll(splitIntoLines(chunk))
        
        return displayLines.joinToString("\n")
    }
    
    /**
     * Weave user phrase into monologue based on metrics
     * This is the core of Molly's response mechanism
     */
    fun weavePhrase(userInput: String): String {
        if (userInput.isBlank()) return getNextChunk()
        
        // Split user input into fragments
        val fragments = MollyMetrics.splitFragments(userInput)
        if (fragments.isEmpty()) return getNextChunk()
        
        // Store fragments in database
        fragments.forEach { fragment ->
            val metrics = MollyMetrics.computeMetrics(fragment)
            db.storeLine(fragment, metrics)
        }
        
        // Get next chunk
        val chunkSize = CHARS_PER_LINE * LINES_TO_DISPLAY
        val endPos = min(currentPosition + chunkSize, monologueText.length)
        var chunk = monologueText.substring(currentPosition, endPos)
        
        // Select fragment to weave (highest resonance)
        val fragment = selectFragmentToWeave(fragments)
        
        // Find insertion point based on metrics
        val insertPos = findInsertionPoint(chunk, fragment)
        
        // Clean fragment (remove punctuation as in original Molly)
        val cleanFragment = fragment.uppercase().replace(Regex("[^A-Z0-9\\s]"), "")
        
        // Insert fragment (may break words!)
        chunk = chunk.substring(0, insertPos) + 
                " $cleanFragment " + 
                chunk.substring(insertPos)
        
        // Update position
        currentPosition = endPos
        if (currentPosition >= monologueText.length) {
            currentPosition = 0
        }
        
        // Split into display lines
        displayLines.clear()
        displayLines.addAll(splitIntoLines(chunk))
        
        return displayLines.joinToString("\n")
    }
    
    /**
     * Select fragment with highest resonance score
     */
    private fun selectFragmentToWeave(fragments: List<String>): String {
        return fragments.maxByOrNull { fragment ->
            val metrics = MollyMetrics.computeMetrics(fragment)
            metrics.perplexity + metrics.resonance
        } ?: fragments.first()
    }
    
    /**
     * Find insertion point in chunk based on semantic similarity
     * Uses simple heuristic: look for similar word patterns
     */
    private fun findInsertionPoint(chunk: String, fragment: String): Int {
        if (chunk.isEmpty()) return 0
        
        val fragmentWords = fragment.lowercase().split(Regex("\\s+"))
        val chunkWords = chunk.lowercase().split(Regex("\\s+"))
        
        var bestScore = 0.0
        var bestPos = chunk.length / 2 // default to middle
        
        var charPos = 0
        for (i in chunkWords.indices) {
            // Calculate similarity score
            val score = calculateSimilarity(
                chunkWords.subList(maxOf(0, i - 2), minOf(chunkWords.size, i + 3)),
                fragmentWords
            )
            
            if (score > bestScore) {
                bestScore = score
                bestPos = charPos
            }
            
            charPos += chunkWords[i].length + 1
        }
        
        // Add some randomness
        val randomOffset = Random.nextInt(-10, 11)
        bestPos = (bestPos + randomOffset).coerceIn(0, chunk.length)
        
        return bestPos
    }
    
    /**
     * Calculate simple word overlap similarity
     */
    private fun calculateSimilarity(context: List<String>, fragment: List<String>): Double {
        if (context.isEmpty() || fragment.isEmpty()) return 0.0
        
        val contextSet = context.toSet()
        val fragmentSet = fragment.toSet()
        val overlap = contextSet.intersect(fragmentSet).size
        
        return overlap.toDouble() / (contextSet.size + fragmentSet.size)
    }
    
    /**
     * Split chunk into display lines (~80 chars each)
     */
    private fun splitIntoLines(text: String): List<String> {
        val lines = mutableListOf<String>()
        val words = text.split(Regex("\\s+"))
        
        var currentLine = StringBuilder()
        for (word in words) {
            if (currentLine.length + word.length + 1 > CHARS_PER_LINE && currentLine.isNotEmpty()) {
                lines.add(currentLine.toString())
                currentLine = StringBuilder()
            }
            
            if (currentLine.isNotEmpty()) {
                currentLine.append(" ")
            }
            currentLine.append(word)
        }
        
        if (currentLine.isNotEmpty()) {
            lines.add(currentLine.toString())
        }
        
        // Return last LINES_TO_DISPLAY lines
        return lines.takeLast(LINES_TO_DISPLAY)
    }
    
    /**
     * Integrate with resonance.sqlite3 from ariannamethod ecosystem
     * This allows Molly to respond to system-wide events
     */
    fun integrateResonance(): String? {
        val resonanceLines = db.getResonanceLines(5)
        if (resonanceLines.isEmpty()) return null
        
        // Pick random line from resonance
        val line = resonanceLines.random()
        return weavePhrase(line)
    }
}
