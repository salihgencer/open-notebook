"""TSG LLM Extractor — Ticaret Sicil Gazetesi ilanlarından yapısal veri çıkarır."""

import json
import os
import re
from pathlib import Path
from typing import Dict, Optional

import yaml

# Prompts dizininin yolu
PROMPTS_DIR = Path(__file__).parent / "prompts"


def load_prompt(prompt_name: str) -> str:
    """
    YAML prompt dosyasını yükler ve 'prompt' alanını döndürür.

    Args:
        prompt_name: Prompt dosyasının adı (uzantısız, ör. "triage", "genel")

    Returns:
        Prompt metni

    Raises:
        FileNotFoundError: Dosya bulunamazsa
        KeyError: 'prompt' alanı yoksa
    """
    prompt_path = PROMPTS_DIR / f"{prompt_name}.yaml"

    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt dosyası bulunamadı: {prompt_path}")

    with open(prompt_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if "prompt" not in data:
        raise KeyError(f"'prompt' alanı bulunamadı: {prompt_path}")

    return data["prompt"]


async def call_llm(prompt: str, model_id: Optional[str] = None) -> str:
    """
    LLM'e prompt gönderir ve yanıt metnini döndürür.

    Args:
        prompt: LLM'e gönderilecek prompt metni
        model_id: Kullanılacak model ID'si (None ise varsayılan chat modeli)

    Returns:
        LLM'den gelen yanıt metni
    """
    from open_notebook.ai.models import model_manager

    if model_id:
        model = await model_manager.get_model(model_id)
    else:
        model = await model_manager.get_default_model("chat")

    if model is None:
        raise RuntimeError("LLM modeli yapılandırılmamış. Ayarlar → Modeller bölümünden varsayılan chat modelini ayarlayın.")

    response = await model.achat_complete(
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content


def parse_json_response(text: str) -> Dict:
    """
    LLM yanıtından JSON çıkarır.

    Markdown kod bloklarını, düz JSON'u ve metin içine gömülü JSON'u destekler.

    Args:
        text: LLM'den gelen ham yanıt metni

    Returns:
        Ayrıştırılmış JSON dict

    Raises:
        ValueError: Geçerli JSON bulunamazsa
    """
    if not text or not text.strip():
        raise ValueError("Boş yanıt metni")

    # Markdown kod bloklarını temizle (```json ... ``` veya ``` ... ```)
    # Kapanmayan code block'u da handle et
    md_pattern = r"```(?:json)?\s*([\s\S]*?)(?:\s*```|$)"
    md_match = re.search(md_pattern, text)
    if md_match:
        json_str = md_match.group(1).strip()
        # İçinden JSON çıkar
        first = json_str.find("{")
        last = json_str.rfind("}")
        if first >= 0 and last > first:
            try:
                return json.loads(json_str[first:last + 1])
            except json.JSONDecodeError:
                pass

    # Düz JSON (ilk { ile son } arasını çıkar)
    stripped = text.strip()
    if stripped.startswith("{"):
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            pass

    # Metin içindeki ilk { ile son } arasını dene
    first_brace = text.find("{")
    last_brace = text.rfind("}")

    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        json_str = text[first_brace:last_brace + 1]
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass

    # Son çare: tüm JSON benzeri blokları bul, en büyüğünü dene
    json_blocks = re.findall(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
    if json_blocks:
        longest = max(json_blocks, key=len)
        try:
            return json.loads(longest)
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Geçerli JSON bulunamadı. Yanıt: {text[:200]}...")


async def triage_extract(announcement_text: str) -> Dict:
    """
    Aşama 4a: İlan metninden hızlı triage çıkarımı yapar.

    triage.yaml promptunu kullanır ve temel ilan bilgilerini döndürür.

    Args:
        announcement_text: TSG ilan metni

    Returns:
        islem_turu, gazette_date, gazette_no, ilan_kodu, sirket_unvani, mersis_no alanlarını içeren dict
    """
    prompt_template = load_prompt("triage")
    prompt = prompt_template.replace("{text}", announcement_text)

    response_text = await call_llm(prompt)
    return parse_json_response(response_text)


async def detail_extract(announcement_text: str, islem_turu: str) -> Dict:
    """
    Aşama 4b: İlan metninden detaylı yapısal veri çıkarımı yapar.

    İşlem türüne özgü prompt varsa onu, yoksa genel.yaml'i kullanır.
    JSON parse başarısızsa 1 kez retry yapar.

    Args:
        announcement_text: TSG ilan metni
        islem_turu: Triage aşamasından gelen işlem türü

    Returns:
        fields, persons, events, articles, delil_belgesi alanlarını içeren dict
    """
    try:
        prompt_template = load_prompt(islem_turu)
    except FileNotFoundError:
        prompt_template = load_prompt("genel")

    prompt = prompt_template.replace("{text}", announcement_text).replace(
        "{islem_turu}", islem_turu
    )

    response_text = await call_llm(prompt)
    try:
        return parse_json_response(response_text)
    except ValueError:
        # Retry: LLM'e düzeltme isteği
        retry_prompt = (
            "Aşağıdaki yanıtı geçerli bir JSON objesine dönüştür. "
            "SADECE JSON döndür, başka metin ekleme.\n\n"
            f"{response_text[:3000]}"
        )
        retry_text = await call_llm(retry_prompt)
        return parse_json_response(retry_text)
