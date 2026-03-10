# Plan: Migrate from google-generativeai (Deprecated) to google-genai

## Summary

**Status**: `google-generativeai` package **END-OF-LIFE** (Nov 30, 2025) - we're in March 2026, using deprecated package
**Replacement**: `google-genai` v1.66.0 (released Mar 5, 2026) with breaking API changes
**User Request**: "Check carefully if it is migrated or not" - verified migration is required

**Approach**: Update 2 files (`api_client.py`, `agent.py`) + `requirements.txt` to use new SDK with Client-based API

## Steps

### Phase 1: Discovery - Current Usage Mapping ✅ COMPLETE

**Finding**: 2 projects affected (`1-3_7-3/` and `1-12_13-12/`), focusing on `1-3_7-3/` first

**Current Pattern in `1-3_7-3/`:**
```python
# api_client.py line 67
genai.configure(api_key=google_key)  # Global config, no return value

# agent.py lines 66-69  
self.model = genai.GenerativeModel(
    model_name=model_name,
    system_instruction=system_prompt
)
self.chat = self.model.start_chat(history=[])

# agent.py line 117
response = self.chat.send_message(prompt)
return response.text.strip()

# agent.py line 217 (clear context)
self.chat = self.model.start_chat(history=[])
```

### Phase 2: New API Design - Migration Mapping

**New Pattern for `google-genai`:**
```python
# api_client.py - initialization
self.google_client = genai.Client(api_key=google_key)
return (self.provider, self.client, self.model_name, self.google_client)

# agent.py - initialization  
if api_provider == "google":
    self.google_client = google_client  # Store client instance
    self.chat = google_client.chats.create(
        model=model_name,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt
        )
    )

# agent.py - generation
response = self.chat.send_message(prompt)
return response.text  # Check if .strip() still needed

# agent.py - clear context
self.chat = self.google_client.chats.create(
    model=self.model_name,
    config=types.GenerateContentConfig(
        system_instruction=self.system_prompt
    )
)
```

### Phase 3: Update Implementation (*depends on Phase 2*)

3. **Update multiagent_classroom/api_client.py** - Change initialization pattern
   - Line 11: Change `import google.generativeai as genai` → `from google import genai`
   - Line 67: Replace `genai.configure(api_key=google_key)` with `self.google_client = genai.Client(api_key=google_key)`
   - Lines 43-48: Update return type of `initialize()` to return `Tuple[str, Optional[OpenAI], str, Optional[genai.Client]]`
   - Add `self.google_client` attribute to store Google client instance
   - Update `get_client()` method or add `get_google_client()` method

4. **Update multiagent_classroom/agent.py** - Migrate to client-based chat API
   - Line 11: Change `import google.generativeai as genai` → `from google import genai; from google.genai import types`
   - Lines 32-34: Update class attributes documentation for new client pattern
   - Constructor signature: Add `google_client: Optional[genai.Client] = None` parameter (line 45)
   - Lines 65-69: Replace GenerativeModel with chat creation:
     ```python
     if api_provider == "google":
         self.google_client = google_client
         self.chat = google_client.chats.create(
             model=model_name,
             config=types.GenerateContentConfig(
                 system_instruction=system_prompt
             )
         )
     ```
   - Line 117: Keep `response = self.chat.send_message(prompt)` unchanged (same method signature)
   - Line 217: Update `clear_context()` to recreate chat session with client:
     ```python
     if self.api_provider == "google":
         self.chat = self.google_client.chats.create(
             model=self.model_name,
             config=types.GenerateContentConfig(
                 system_instruction=self.system_prompt
             )
         )
     ```

5. **Update main.py** - Pass Google client to agents
   - Line 92 area (`_initialize_components`): Unpack 4 values instead of 3:
     ```python
     self.api_provider, self.client, self.model_name, self.google_client = self.api_client.initialize()
     ```
   - Lines 150-155 (`_create_agent`): Pass `google_client` parameter to SimpleAgent constructor

6. **Update requirements.txt** - Switch package
   - Line 2: Change `google-generativeai==0.8.5` → `google-genai>=1.66.0`

### Phase 4: Testing (*depends on Phase 3*)

7. **Installation test** - Verify new package installs correctly
   - Uninstall old: `pip uninstall google-generativeai -y`
   - Install new: `pip install google-genai>=1.66.0`
   - Import test: `python -c "from google import genai; from google.genai import types; print('OK')"`

8. **Unit test existing pytest suite** - Ensure no regressions
   - `pytest tests/ -v` should pass all 23 tests
   - Note: Tests don't use Google API, should be unaffected

9. **Integration test Google API** - Verify chat functionality
   - Set GOOGLE_API_KEY in .env
   - Run simulation: `python main.py` (select Google when asked)
   - Verify: Scenarios execute, responses generated, no errors
   - Check: Chat history maintained across turns in conversation

10. **End-to-end validation** - Compare outputs
    - Run same scenario with DeepSeek: Verify still works
    - Run same scenario with Google: Verify results format unchanged
    - Compare log files: Should have similar structure

### Phase 5: Documentation (*parallel with Phase 4*)

11. **Update README.md** - Reflect new package
    - Installation section: Mention `google-genai` if package name appears
    - API key section: Verify Google Gemini link still accurate
    - Add migration note to Future Improvements or Changelog section

## Relevant Files

- [multiagent_classroom/api_client.py](1-3_7-3/multiagent_classroom/api_client.py) - Initialize Google client (lines 11, 65-69)
  * Line 11: `import google.generativeai as genai` → Change to `from google import genai`
  * Lines 65-69: `genai.configure(api_key)` → Replace with `genai.Client(api_key)` pattern
  * Return value: Need to return client instance instead of None

- [multiagent_classroom/agent.py](1-3_7-3/multiagent_classroom/agent.py) - Use Google GenerativeModel (lines 11, 65-70, 107-118)
  * Line 11: `import google.generativeai as genai` → Change to `from google import genai`
  * Lines 65-70: `genai.GenerativeModel()` → Update to use client-based chat creation
  * Lines 107-118: `_generate_google_response()` → Update chat.send_message() usage
  * Constructor: Accept client parameter if using google provider

- [requirements.txt](1-3_7-3/requirements.txt) - Package dependency (line 2)
  * Line 2: `google-generativeai==0.8.5` → Change to `google-genai>=1.66.0`

- [README.md](1-3_7-3/README.md) - Documentation
  * Line 30: Google Gemini API link → Verify still accurate
  * Installation section → Update if package name mentioned

## Verification

1. **Package installation test**
   - `pip uninstall google-generativeai`
   - `pip install google-genai>=1.66.0`
   - Verify: `python -c "from google import genai; print(genai.__version__)"`

2. **API initialization test**
   - Set GOOGLE_API_KEY in .env
   - Run: `python -c "from multiagent_classroom import APIClient; api = APIClient(); api.initialize()"`
   - Should initialize without ModuleNotFoundError

3. **Full simulation test**
   - `python main.py` with Google API key
   - Verify scenarios execute successfully
   - Verify logs/ and results/ files generated
   - Compare output format with previous runs using DeepSeek

4. **Pytest regression test**
   - `pytest tests/ -v`
   - All 23 tests should pass (reliability_metrics tests don't use Google API)

## Decisions

- **Migration Required**: YES - `google-generativeai` is EOL (Nov 30, 2025), currently Mar 2026
- **Breaking Changes**: YES - API namespace changed, client pattern different
- **Backward Compatibility**: NO - Cannot keep old package, must fully migrate
- **Scope**: Update Google API usage only, DeepSeek/OpenAI code unchanged

## Further Considerations

1. **Chat API Equivalence**: Need to confirm `client.chats.create()` + `chat.send_message()` maintains conversation state like old `model.start_chat()`
   - Recommendation: Test multi-turn conversations in agent.py after migration
   - Alternative: Use `client.models.generate_content()` with explicit history management

2. **Client Lifecycle**: New SDK uses client-based pattern - should we close clients explicitly?
   - Recommendation A: Use context manager pattern `with genai.Client() as client:`
   - Recommendation B: Keep current pattern, add explicit `client.close()` in cleanup
   - Recommendation C: Ignore cleanup for short-lived scripts (current approach)


3. **Secondary Project `1-12_13-12/`**: Same deprecated package usage found
   - Files affected: `1-12_13-12/main.py` (line 8, 26), `1-12_13-12/src/agents.py` (line 9, 35-42, 89)
   - Should we migrate this project too? Or focus only on `1-3_7-3/` first?
   - Recommendation: Migrate `1-3_7-3/` first, test thoroughly, then apply same pattern to `1-12_13-12/`

   - Files affected: `1-12_13-12/main.py` (line 8, 26), `1-12_13-12/src/agents.py` (line 9, 35-42, 89)
   - Should we migrate this project too? Or focus only on `1-3_7-3/` first?
   - Recommendation: Migrate `1-3_7-3/` first, then apply same pattern to `1-12_13-12/`

