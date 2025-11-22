================================================================================
PROPOSAL: IMPROVING GOOGLE TRANSLATION API PRECISION
================================================================================

Project: EmailReader
Component: Google Cloud Translation API v3 Integration
Last Updated: 2025-11-19

================================================================================
EXECUTIVE SUMMARY
================================================================================

Based on analysis of the current implementation and Google Cloud Translation
API v3 capabilities, this proposal identifies 12 actionable improvements to
maximize translation precision. The current implementation uses basic API calls
without leveraging advanced features available in the API.

================================================================================
CURRENT STATE ANALYSIS
================================================================================

WHAT WE'RE USING:
✓ Google Cloud Translation API v3
✓ Document translation endpoint (preserves formatting)
✓ Text translation endpoint (for paragraph batches)
✓ Auto-detection of source language
✓ Basic error handling and retry logic

WHAT WE'RE NOT USING:
✗ Custom glossaries for domain-specific terminology
✗ Translation LLM model (using default NMT)
✗ Adaptive Translation for context preservation
✗ Model selection parameters
✗ Contextual glossary features
✗ Source language specification (always auto-detect)
✗ Custom translation models (AutoML)
✗ Batch translation optimization
✗ Translation hints/context

================================================================================
PROPOSED IMPROVEMENTS (RANKED BY IMPACT)
================================================================================

TIER 1: HIGH IMPACT, LOW EFFORT
--------------------------------

1. ENABLE TRANSLATION LLM MODEL
   Impact: HIGH | Effort: LOW | Cost: Moderate increase

   Current: No model specified - uses default NMT

   Proposed: Specify Translation LLM model explicitly

   Benefits:
   - Fine-tuned from Gemini foundation models
   - Highest quality translation available
   - Better context understanding
   - Improved handling of idiomatic expressions
   - ~3x faster than Gemini 2.0 Flash

   Configuration:
   "translation": {
     "google_doc": {
       "model": "translation-llm",  // NEW
       "location": "us-central1"     // Changed from "global"
     }
   }

2. SPECIFY SOURCE LANGUAGE (AVOID AUTO-DETECTION)
   Impact: MEDIUM | Effort: LOW | Cost: None

   Current: Always auto-detects source language

   Problem: Auto-detection can be wrong, especially for:
   - Short texts
   - Mixed-language documents
   - Similar languages (Russian/Ukrainian, Spanish/Portuguese)

   Proposed: Pass detected language from langdetect to API

   Benefits:
   - Eliminates auto-detection errors
   - Faster processing (no detection step)
   - More predictable results

TIER 2: MEDIUM IMPACT, MEDIUM EFFORT
------------------------------------

3. IMPLEMENT CUSTOM GLOSSARIES
   Impact: HIGH | Effort: MEDIUM | Cost: Minimal

   Purpose: Ensure consistent, accurate translation of:
   - Legal terminology (e.g., "plaintiff", "defendant", "subpoena")
   - Named entities (person names, organization names)
   - Technical terms specific to your domain
   - Acronyms and abbreviations

   Example Glossary (CSV format):
   истец,plaintiff
   ответчик,defendant
   повестка,subpoena
   федерация тенниса россии,Russian Tennis Federation
   артем строкань,Artem Strokan

   Implementation:
   1. Create glossary file (CSV/TSV)
   2. Upload to Google Cloud Storage
   3. Create glossary resource via API
   4. Reference in translation requests

   Benefits:
   - 100% consistency for defined terms
   - Prevents mistranslation of proper nouns
   - Maintains legal terminology accuracy
   - Context-aware with LLM enhancement

4. USE ADAPTIVE TRANSLATION WITH REFERENCE PAIRS
   Impact: MEDIUM-HIGH | Effort: MEDIUM | Cost: Moderate

   Purpose: Train the model on your specific translation style using example
   pairs

   Example Reference Pairs:
   Source (RU): "Я убеждена, что вклад Артема Строконя в развитие тенниса..."
   Reference (EN): "I am convinced that Artem Strokan's contribution to the
                    development of tennis..."

   Benefits:
   - Learns your preferred translation style
   - Better context preservation
   - Domain-specific accuracy
   - Translates whole paragraphs at once (not sentence-by-sentence)

5. IMPLEMENT MULTI-SENTENCE CONTEXT WINDOWS
   Impact: MEDIUM | Effort: LOW | Cost: None

   Current Problem: Text batch translation joins paragraphs with delimiter but
   doesn't provide semantic context

   Proposed: Provide surrounding context (previous and next paragraph snippets)
   with each translation request

   Benefits:
   - Better pronoun resolution
   - Consistent terminology across paragraphs
   - Improved coherence

6. ADD QUALITY VERIFICATION LAYER
   Impact: MEDIUM | Effort: MEDIUM | Cost: None (uses existing API)

   Proposed: Implement back-translation verification for critical documents

   Process:
   1. Translate document A→B
   2. Back-translate B→A
   3. Compare original A with back-translated A
   4. Calculate similarity score
   5. Flag low-quality translations for human review

   Benefits:
   - Catches poor translations
   - Provides quality metrics
   - Enables human review triggers

TIER 3: HIGH IMPACT, HIGH EFFORT
---------------------------------

7. CREATE CUSTOM AUTOML TRANSLATION MODEL
   Impact: VERY HIGH | Effort: HIGH | Cost: High (training cost)

   Purpose: Train a custom model specifically for your domain (legal documents,
   tennis federation correspondence)

   Process:
   1. Collect 10,000+ sentence pairs (Russian-English)
   2. Focus on legal and sports domain
   3. Train AutoML Translation model
   4. Use custom model in API requests

   Benefits:
   - Maximum accuracy for your specific domain
   - Learns your organization's terminology
   - Handles unique document types
   - Long-term precision improvement

8. IMPLEMENT LOCATION-SPECIFIC ENDPOINTS
   Impact: LOW-MEDIUM | Effort: LOW | Cost: None

   Current: Using location: "global"

   Proposed: Use region-specific endpoints for lower latency

   Configuration:
   "translation": {
     "google_doc": {
       "location": "us-central1",
       "endpoint": "us-central1-translate.googleapis.com"
     }
   }

   Benefits:
   - Lower latency
   - Better SLA
   - Regional data residency compliance

TIER 4: ADDITIONAL OPTIMIZATIONS
---------------------------------

9. OPTIMIZE BATCH SIZES FOR TRANSLATION LLM
   Current: batch_size: 15

   Proposed: Dynamic batch sizing based on content length

   Logic:
   - avg_length < 100 chars → batch_size = 25 (short paragraphs)
   - avg_length < 500 chars → batch_size = 15 (medium paragraphs)
   - avg_length >= 500 chars → batch_size = 5 (long paragraphs)

10. ADD TRANSLATION CONFIDENCE SCORES
    Proposed: Log and track confidence scores from API

    Implementation:
    - Extract confidence from API response
    - Log confidence scores
    - Flag translations with confidence < 0.80

11. IMPLEMENT CACHING FOR REPEATED CONTENT
    Proposed: Cache common translations to reduce API calls

    Implementation:
    - Hash paragraph text
    - Check cache before API call
    - Store translations with TTL (e.g., 1 week)

12. ADD PREPROCESSING FOR SPECIAL CHARACTERS
    Proposed: Normalize text before translation

    Processing:
    - Normalize quotes: " " → " "
    - Normalize dashes: — – → -
    - Preserve intentional formatting (numbers, dates, emails, URLs)

================================================================================
IMPLEMENTATION PRIORITY MATRIX
================================================================================

Priority | Improvement                    | Impact | Effort | Cost   | Timeline
---------|--------------------------------|--------|--------|--------|----------
P0       | Translation LLM Model          | HIGH   | LOW    | Medium | 1 day
P0       | Specify Source Language        | MEDIUM | LOW    | None   | 1 day
P1       | Custom Glossaries              | HIGH   | MEDIUM | Low    | 1 week
P1       | Multi-Sentence Context         | MEDIUM | LOW    | None   | 2 days
P2       | Adaptive Translation           | MEDIUM | MEDIUM | Medium | 2 weeks
P2       | Quality Verification           | MEDIUM | MEDIUM | None   | 3 days
P2       | Optimize Batch Sizes           | LOW    | LOW    | None   | 1 day
P3       | Location Endpoints             | LOW    | LOW    | None   | 1 day
P3       | Confidence Scores              | LOW    | LOW    | None   | 2 days
P3       | Translation Caching            | MEDIUM | MEDIUM | None   | 3 days
P4       | Preprocessing                  | LOW    | LOW    | None   | 2 days
P5       | Custom AutoML Model            | V.HIGH | HIGH   | High   | 4-6 weeks

================================================================================
RECOMMENDED IMPLEMENTATION PLAN
================================================================================

PHASE 1 (WEEK 1): QUICK WINS
-----------------------------
1. Enable Translation LLM model
2. Add source language specification
3. Optimize batch sizes
4. Add confidence score logging

Expected Impact: 15-25% accuracy improvement

PHASE 2 (WEEKS 2-3): GLOSSARY IMPLEMENTATION
--------------------------------------------
1. Create legal/sports terminology glossary
2. Upload to Cloud Storage
3. Configure glossary in API calls
4. Enable contextual glossary features

Expected Impact: 20-35% improvement on domain-specific terms

PHASE 3 (WEEKS 4-6): ADVANCED FEATURES
---------------------------------------
1. Implement adaptive translation
2. Add quality verification layer
3. Multi-sentence context windows
4. Translation caching

Expected Impact: Additional 10-15% improvement

PHASE 4 (MONTHS 2-3): CUSTOM MODEL (OPTIONAL)
----------------------------------------------
1. Collect training data (10,000+ pairs)
2. Train AutoML model
3. A/B test against LLM model
4. Deploy custom model

Expected Impact: 30-50% improvement for domain-specific content

================================================================================
COST ANALYSIS
================================================================================

Current Monthly Cost: $X (based on volume)

Projected Costs with Improvements:

Feature                    | Cost Impact  | Notes
---------------------------|--------------|---------------------------------------
Translation LLM            | +20-30%      | Higher quality, slightly more expensive
Glossaries                 | <1%          | Minimal cost (storage + lookup)
Adaptive Translation       | +10-15%      | Training dataset overhead
Quality Verification       | +100% calls  | Only for critical documents
Custom AutoML              | $1000-3000   | One-time training + ongoing inference
Location Endpoints         | 0%           | No cost change
Batch Optimization         | -5-10%       | Fewer API calls
Caching                    | -10-20%      | Reduced API usage

ROI: Significantly fewer manual corrections, improved client satisfaction,
reduced re-translation costs

================================================================================
CONFIGURATION CHANGES REQUIRED
================================================================================

File: credentials/config.dev.json

{
  "translation": {
    "provider": "google_doc",
    "google_doc": {
      "project_id": "synologysafeaccess-320003",
      "location": "us-central1",  // Changed from "global"
      "endpoint": "us-central1-translate.googleapis.com",
      "use_service_account": true,
      "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",

      // NEW PARAMETERS
      "model": "translation-llm",
      "use_glossary": true,
      "glossary_id": "legal-sports-ru-en",
      "specify_source_language": true,
      "default_source_language": "ru",
      "enable_adaptive_translation": true,
      "adaptive_dataset_id": "tennis-legal-dataset",
      "quality_verification": {
        "enabled": true,
        "threshold": 0.70,
        "back_translate_on_low_confidence": true
      },
      "batch_optimization": {
        "dynamic_sizing": true,
        "max_batch_size": 25,
        "min_batch_size": 5
      },
      "caching": {
        "enabled": true,
        "ttl_hours": 168  // 1 week
      }
    }
  }
}

================================================================================
SUCCESS METRICS
================================================================================

BEFORE IMPLEMENTATION:
- Translation accuracy: ~85-90% (estimated)
- Manual corrections required: High
- Consistency: Variable
- Processing time: Baseline

TARGET AFTER PHASE 1-2:
- Translation accuracy: 95-98%
- Manual corrections: Minimal
- Consistency: High (glossary-enforced)
- Processing time: Similar or faster

TARGET AFTER PHASE 3-4:
- Translation accuracy: 98-99%
- Manual corrections: Rare
- Consistency: Very high
- Domain-specific terms: 100% accurate

================================================================================
TECHNICAL IMPLEMENTATION DETAILS
================================================================================

1. TRANSLATION LLM MODEL CONFIGURATION

   Code Location: src/translation/google_doc_translator.py

   Current API Call:
   request = translate_v3.TranslateDocumentRequest(
       parent=self.parent,
       target_language_code=target_lang,
       document_input_config=document_input_config
   )

   Updated API Call:
   model_path = f"projects/{self.project_id}/locations/{self.location}/models/general/translation-llm"

   request = translate_v3.TranslateDocumentRequest(
       parent=self.parent,
       target_language_code=target_lang,
       document_input_config=document_input_config,
       model=model_path  // NEW: Specify Translation LLM
   )

2. SOURCE LANGUAGE SPECIFICATION

   Chain of Changes:

   A. Document Processor (src/process_documents.py)
      detected_lang = detect(text)
      translate_document_to_english(
          original_file_path, new_file_path,
          source_lang=detected_lang,  // NEW
          target_lang=target_lang
      )

   B. Translation Utility (src/utils.py)
      def translate_document_to_english(
          original_path, translated_path,
          source_lang=None,  // NEW
          target_lang=None
      ):
          translator.translate_document(
              input_path=original_path,
              output_path=translated_path,
              source_lang=source_lang,  // Pass through
              target_lang=target
          )

   C. Translator Method (src/translation/google_doc_translator.py)
      def translate_document(
          self, input_path, output_path,
          source_lang=None,  // NEW
          target_lang='en'
      ):
          translated_content = self._call_translation_api(
              document_content, target_lang, source_lang)

   D. API Call (already supported in _call_translation_api)
      request = translate_v3.TranslateDocumentRequest(
          parent=self.parent,
          source_language_code=source_lang,  // Use it
          target_language_code=target_lang,
          document_input_config=document_input_config
      )

3. GLOSSARY IMPLEMENTATION

   Step 1: Create Glossary Resource
   glossary = translate_v3.Glossary(
       name=f"projects/{project}/locations/us-central1/glossaries/legal-ru-en",
       language_pair=translate_v3.Glossary.LanguagePair(
           source_language_code="ru",
           target_language_code="en"
       ),
       input_config=translate_v3.GlossaryInputConfig(
           gcs_source=translate_v3.GcsSource(
               input_uri="gs://bucket/glossaries/legal_ru_en.csv"
           )
       )
   )

   Step 2: Use in Translation
   glossary_config = translate_v3.TranslateTextGlossaryConfig(
       glossary=f"projects/{project}/locations/us-central1/glossaries/legal-ru-en",
       ignore_case=False,
       contextual_translation_enabled=True  // LLM enhancement
   )

   request = translate_v3.TranslateDocumentRequest(
       parent=self.parent,
       target_language_code=target_lang,
       document_input_config=document_input_config,
       glossary_config=glossary_config
   )

================================================================================
NEXT STEPS
================================================================================

1. Review and approve this proposal
2. Prioritize which improvements to implement first
3. Allocate budget for Translation LLM and optional AutoML training
4. Create glossary of legal/sports terms (can start with 50-100 entries)
5. Begin Phase 1 implementation (1 week timeline)

================================================================================
QUESTIONS FOR CONSIDERATION
================================================================================

1. Which languages are most critical? (Russian→English only, or others?)
2. Budget for AutoML training? ($1000-3000 one-time cost)
3. Glossary ownership? (Who maintains the terminology list?)
4. Quality thresholds? (What accuracy level is acceptable?)
5. Timeline urgency? (Quick wins vs. comprehensive solution?)

================================================================================
CONCLUSION
================================================================================

This proposal provides a clear roadmap to maximum translation precision using
Google Cloud Translation API v3's advanced features. The phased approach allows
for incremental improvements with measurable results at each stage.

Phase 1 and 2 improvements (Translation LLM + Source Language + Glossaries)
can be implemented within 3 weeks and are expected to deliver 35-60% accuracy
improvement with minimal cost increase.

================================================================================
END OF DOCUMENT
================================================================================
