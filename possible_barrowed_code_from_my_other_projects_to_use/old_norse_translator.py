#!/usr/bin/env python3
"""
Old Norse Translation Tool
==========================

Translates Old Norse text into authentic Norse Pagan Viking poetry.
Uses OpenRouter API with configurable models.

Features:
- Line-by-line translation with poetic rendering
- Preserves kennings and Norse imagery
- Outputs to JSON format
- Configurable via separate config file
- Progress display

Usage:
    python old_norse_translator.py input.txt output.json
    python old_norse_translator.py --help
"""

import json
import yaml
import argparse
import sys
import time
from pathlib import Path
from typing import Dict, Optional
import httpx


class OldNorseTranslator:
    """Translates Old Norse text using AI."""
    
    OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
    
    def __init__(self, config_path: str = "translator_config.yaml"):
        """
        Initialize translator.
        
        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        self.api_key = self.config.get("openrouter_api_key", "")
        self.model = self.config.get("model", "deepseek/deepseek-chat")
        self.max_retries = self.config.get("max_retries", 3)
        self.delay_between_calls = self.config.get("delay_between_calls", 0.5)
        
        if not self.api_key:
            raise ValueError("No OpenRouter API key found in config file")
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration file."""
        path = Path(config_path)
        if not path.exists():
            # Create default config
            default_config = {
                "openrouter_api_key": "YOUR_OPENROUTER_API_KEY_HERE",
                "model": "deepseek/deepseek-chat",
                "max_retries": 3,
                "delay_between_calls": 0.5,
                "style": {
                    "preserve_kennings": True,
                    "use_alliteration": True,
                    "poetic_style": "eddic",
                    "add_notes": True
                }
            }
            with open(path, 'w', encoding='utf-8') as f:
                yaml.dump(default_config, f, default_flow_style=False)
            print(f"Created default config at {path}")
            print("Please add your OpenRouter API key to the config file.")
            sys.exit(1)
        
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _call_api(self, prompt: str, system_prompt: str) -> Optional[str]:
        """Make API call to OpenRouter."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/norse-saga-engine",
            "X-Title": "Old Norse Translator"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        for attempt in range(self.max_retries):
            try:
                with httpx.Client(timeout=60.0) as client:
                    response = client.post(
                        self.OPENROUTER_URL,
                        headers=headers,
                        json=payload
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        return data["choices"][0]["message"]["content"]
                    else:
                        print(f"API error: {response.status_code} - {response.text}")
                        
            except Exception as e:
                print(f"Request failed (attempt {attempt + 1}): {e}")
                time.sleep(2 ** attempt)  # Exponential backoff
        
        return None
    
    def translate_line(self, old_norse_line: str, context: str = "") -> Dict:
        """
        Translate a single line of Old Norse.
        
        Args:
            old_norse_line: The Old Norse text to translate
            context: Optional context about the source (saga name, stanza number, etc.)
            
        Returns:
            Dict with translation data
        """
        style_config = self.config.get("style", {})
        
        system_prompt = """You are a master translator of Old Norse texts, deeply versed in:
- Eddic and Skaldic poetry traditions
- Norse kennings (poetic metaphors)
- The spiritual worldview of Norse Paganism
- Alliterative verse structure
- Viking Age culture and values

Your translations must:
1. Capture the SPIRIT and POWER of the original
2. Use authentic Norse imagery and kennings where appropriate
3. Maintain poetic rhythm and beauty
4. Honor the sacred nature of the texts
5. Avoid Christian or modern influences
6. Sound like authentic Viking poetry

Output format - respond with ONLY this JSON structure, no other text:
{
    "original": "<the Old Norse text>",
    "literal": "<word-for-word translation>",
    "poetic": "<your poetic Norse Pagan rendering>",
    "kennings_used": ["<list any kennings used>"],
    "notes": "<any cultural or mythological notes>"
}"""
        
        prompt = f"""Translate this Old Norse line into powerful Norse Pagan Viking poetry:

Old Norse: {old_norse_line}
{f'Context: {context}' if context else ''}

Remember:
- Make it sound like authentic Viking poetry
- Preserve or create appropriate kennings
- Use alliterative rhythm where natural
- Keep the Norse Pagan spiritual worldview
- NO Christian influences

Respond with ONLY the JSON, no markdown or other text."""
        
        response = self._call_api(prompt, system_prompt)
        
        if response:
            try:
                # Clean up response - remove markdown code blocks if present
                response = response.strip()
                if response.startswith("```"):
                    response = response.split("```")[1]
                    if response.startswith("json"):
                        response = response[4:]
                response = response.strip()
                
                return json.loads(response)
            except json.JSONDecodeError as e:
                print(f"Failed to parse response as JSON: {e}")
                return {
                    "original": old_norse_line,
                    "literal": "",
                    "poetic": response,
                    "kennings_used": [],
                    "notes": "Failed to parse structured response"
                }
        
        return {
            "original": old_norse_line,
            "literal": "",
            "poetic": "[Translation failed]",
            "kennings_used": [],
            "notes": "API call failed"
        }
    
    def translate_file(
        self, 
        input_path: str, 
        output_path: str,
        source_name: str = "Unknown",
        skip_empty: bool = True
    ) -> Dict:
        """
        Translate an entire file of Old Norse text.
        
        Args:
            input_path: Path to input text file
            output_path: Path for output JSON file
            source_name: Name of the source text (e.g., "Völuspá")
            skip_empty: Skip empty lines
            
        Returns:
            Summary statistics
        """
        input_file = Path(input_path)
        if not input_file.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        with open(input_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        translations = []
        stats = {
            "source": source_name,
            "total_lines": len(lines),
            "translated": 0,
            "failed": 0,
            "skipped": 0
        }
        
        print(f"\nTranslating {source_name}...")
        print(f"Total lines: {len(lines)}")
        print("-" * 50)
        
        for i, line in enumerate(lines, 1):
            line = line.strip()
            
            if not line or (skip_empty and not line.strip()):
                stats["skipped"] += 1
                continue
            
            # Skip lines that are just numbers (stanza numbers)
            if line.isdigit():
                stats["skipped"] += 1
                continue
            
            print(f"[{i}/{len(lines)}] Translating: {line[:50]}...")
            
            context = f"{source_name}, line {i}"
            translation = self.translate_line(line, context)
            translation["line_number"] = i
            translation["source"] = source_name
            
            translations.append(translation)
            
            if translation["poetic"] != "[Translation failed]":
                stats["translated"] += 1
            else:
                stats["failed"] += 1
            
            # Rate limiting
            time.sleep(self.delay_between_calls)
        
        # Build output
        output = {
            "metadata": {
                "source": source_name,
                "translated_by": "Old Norse Translator Tool",
                "model": self.model,
                "statistics": stats
            },
            "translations": translations
        }
        
        # Save to file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        print("-" * 50)
        print("Translation complete!")
        print(f"Translated: {stats['translated']}")
        print(f"Failed: {stats['failed']}")
        print(f"Skipped: {stats['skipped']}")
        print(f"Output saved to: {output_path}")
        
        return stats


def main():
    parser = argparse.ArgumentParser(
        description="Translate Old Norse text into Norse Pagan Viking poetry"
    )
    parser.add_argument("input", help="Input text file with Old Norse lines")
    parser.add_argument("output", help="Output JSON file for translations")
    parser.add_argument(
        "--source", "-s",
        default="Unknown",
        help="Name of the source text (e.g., 'Völuspá', 'Hávamál')"
    )
    parser.add_argument(
        "--config", "-c",
        default="translator_config.yaml",
        help="Path to config file (default: translator_config.yaml)"
    )
    parser.add_argument(
        "--single", "-1",
        action="store_true",
        help="Translate a single line from stdin"
    )
    
    args = parser.parse_args()
    
    try:
        translator = OldNorseTranslator(args.config)
        
        if args.single:
            print("Enter Old Norse text to translate:")
            line = input("> ")
            result = translator.translate_line(line, args.source)
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            translator.translate_file(
                args.input,
                args.output,
                source_name=args.source
            )
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
