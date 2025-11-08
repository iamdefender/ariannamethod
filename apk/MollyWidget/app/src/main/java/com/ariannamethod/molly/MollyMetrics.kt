package com.ariannamethod.molly

import kotlin.math.*

/**
 * Metrics calculator ported from molly.py
 * Computes entropy, perplexity, and resonance for text fragments
 */
object MollyMetrics {
    
    private const val CHAR_VOCAB = "abcdefghijklmnopqrstuvwxyz0123456789 ?"
    private val charToIdx = CHAR_VOCAB.withIndex().associate { it.value to it.index }
    private val vocabSize = CHAR_VOCAB.length
    
    // Simple sentiment analyzer (simplified version of VADER)
    private val positiveWords = setOf("love", "good", "beautiful", "wonderful", "amazing", "happy", "joy", "yes")
    private val negativeWords = setOf("hate", "bad", "ugly", "terrible", "awful", "sad", "no", "never")
    
    data class Metrics(
        val entropy: Double,
        val perplexity: Double,
        val resonance: Double
    )
    
    /**
     * Compute metrics for a given line of text
     */
    fun computeMetrics(line: String): Metrics {
        val tokens = Regex("\\w+").findAll(line.lowercase()).map { it.value }.toList()
        
        if (tokens.isEmpty()) {
            return Metrics(0.0, 0.0, 0.0)
        }
        
        // Compute bigram loss for perplexity/entropy
        val ids = line.lowercase().map { charToIdx[it] ?: charToIdx['?']!! }
        val loss = if (ids.size < 2) {
            0.0
        } else {
            computeBigramLoss(ids)
        }
        
        val entropy = loss / ln(2.0) - log2(vocabSize.toDouble())
        val perplexity = exp(loss) / vocabSize
        
        // Compute resonance (emotion + numeric tokens)
        val emotionScore = computeEmotionScore(tokens)
        val numCount = tokens.count { it.all { c -> c.isDigit() } }
        val resonance = abs(emotionScore) + numCount
        
        return Metrics(entropy, perplexity, resonance)
    }
    
    private fun computeBigramLoss(ids: List<Int>): Double {
        // Simplified bigram model
        var totalLoss = 0.0
        for (i in 0 until ids.size - 1) {
            // Uniform distribution assumption for simplicity
            totalLoss += ln(vocabSize.toDouble())
        }
        return totalLoss / (ids.size - 1)
    }
    
    private fun computeEmotionScore(tokens: List<String>): Double {
        var score = 0.0
        for (token in tokens) {
            when {
                token in positiveWords -> score += 0.5
                token in negativeWords -> score -= 0.5
            }
        }
        return score / max(tokens.size, 1)
    }
    
    /**
     * Split text into fragments based on entropy/perplexity thresholds
     * Ported from split_fragments in molly.py
     */
    fun splitFragments(
        text: String,
        entropyThreshold: Double = 2.0,
        perplexityThreshold: Double = 4.0
    ): List<String> {
        val rawLines = text.lines().map { it.trim() }.filter { it.isNotEmpty() }
        val fragments = mutableListOf<String>()
        
        for (line in rawLines) {
            // Split on punctuation
            val parts = line.split(Regex("[.!?]+"))
            
            for (part in parts) {
                val cleaned = part.replace(Regex("[^\\w\\s]"), "").trim()
                if (cleaned.isEmpty()) continue
                
                val words = cleaned.split(Regex("\\s+"))
                val current = mutableListOf<String>()
                
                for (word in words) {
                    val candidate = (current + word).joinToString(" ")
                    val metrics = computeMetrics(candidate)
                    
                    if (metrics.entropy > entropyThreshold || 
                        metrics.perplexity > perplexityThreshold) {
                        if (current.isNotEmpty()) {
                            fragments.add(current.joinToString(" "))
                        }
                        current.clear()
                        current.add(word)
                    } else {
                        current.add(word)
                    }
                }
                
                if (current.isNotEmpty()) {
                    fragments.add(current.joinToString(" "))
                }
            }
        }
        
        return fragments
    }
}
